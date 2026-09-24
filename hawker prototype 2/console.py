#!/usr/bin/env python3
"""Laptop-local operator console for Tray Watch. No Pi HTTP port is opened."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import shutil
import subprocess
import sys
import tarfile
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "console_assets"
FRAMES = HERE / "frames"
CONFIG = HERE / "console-config.json"
JOB_FILE = HERE / "console-job.json"
CANCEL_FILE = HERE / "console-cancel.flag"
SYNC_FILE = HERE / "console-sync.json"
ROSTER = HERE / "dishes.csv"
REPORTS = HERE / "reports"
APPROVED = REPORTS / "approved"
TOKEN = secrets.token_urlsafe(32)
LOCK = threading.RLock()
STOP = threading.Event()
CURRENT = None
CONFIG_DEFAULT = {"host": "traywatch.local", "user": "", "remote_dir": "~/SG-Eco-Hackathon/hawker prototype 2"}


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def atomic_json(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def config():
    return {**CONFIG_DEFAULT, **read_json(CONFIG, {})}


def validate_config(c):
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,253}", c.get("host", "")):
        raise ValueError("Pi host must be a hostname or IP address, without a port or URL")
    if not re.fullmatch(r"[a-z_][a-z0-9_-]{0,31}", c.get("user", "")):
        raise ValueError("Enter the Pi login user")
    p = c.get("remote_dir", "")
    if not p or "\n" in p or "\r" in p or not (p.startswith("~/") or p.startswith("/")):
        raise ValueError("Pi project path must start with ~/ or /")


def remote_dir_expr(p):
    return '"$HOME"/' + shlex.quote(p[2:]) if p.startswith("~/") else shlex.quote(p)


def ssh_command(args):
    c = config()
    validate_config(c)
    target = f'{c["user"]}@{c["host"]}'
    command = "cd " + remote_dir_expr(c["remote_dir"]) + " && python3 pi_bridge.py " + " ".join(shlex.quote(str(a)) for a in args)
    return ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=yes", target, command]


def bridge(*args, timeout=20, binary=False):
    try:
        r = subprocess.run(ssh_command(args), capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise RuntimeError(f"Pi connection failed: {e}") from e
    if r.returncode:
        err = r.stderr.decode("utf-8", "replace").strip()[-1000:]
        out = r.stdout.decode("utf-8", "replace").strip()
        try:
            err = json.loads(out).get("error", err)
        except ValueError:
            pass
        raise RuntimeError(err or f"Pi command failed (exit {r.returncode})")
    if binary:
        return r.stdout
    try:
        data = json.loads(r.stdout)
    except ValueError as e:
        raise RuntimeError("Pi returned unreadable status; check pi_bridge.py on the Pi") from e
    if data.get("ok") is False:
        raise RuntimeError(data.get("error", "Pi command failed"))
    return data


def local_capture():
    p = FRAMES / "frames.csv"
    rows = []
    if p.exists():
        try:
            with p.open(newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
        except (OSError, csv.Error):
            pass
    good = [r for r in rows if int(r.get("bytes") or 0) > 0 and (FRAMES / (str(r.get("seq", "")).zfill(6) + ".jpg")).exists()]
    return {"rows": len(rows), "valid": len(good), "gaps": len(rows) - len(good),
            "latest": good[-1] if good else None, "files": len(list(FRAMES.glob("[0-9][0-9][0-9][0-9][0-9][0-9].jpg"))) if FRAMES.exists() else 0}


def overview():
    remote = None
    error = None
    try:
        remote = bridge("status", timeout=12)
    except Exception as e:
        error = str(e)
    with LOCK:
        job = read_json(JOB_FILE, {"state": "idle"})
    return {"remote": remote, "connection_error": error, "local": local_capture(),
            "mirror": read_json(SYNC_FILE, {}), "job": job, "settings": config(), "server_time": now()}


def job_update(**values):
    with LOCK:
        old = read_json(JOB_FILE, {})
        old.update(values)
        atomic_json(JOB_FILE, old)


def start_job(kind, fn):
    global CURRENT
    with LOCK:
        if CURRENT and CURRENT.is_alive():
            raise ValueError("Another operation is running. Wait for it or cancel it.")
        STOP.clear()
        CANCEL_FILE.unlink(missing_ok=True)
        job_update(id=secrets.token_hex(4), kind=kind, state="running", started=now(), ended=None, progress="Starting", log=[])

        def run():
            try:
                result = fn()
                job_update(state="cancelled" if STOP.is_set() else "succeeded", progress=result, ended=now())
            except Exception as e:
                job_update(state="cancelled" if STOP.is_set() else "failed", error=str(e), ended=now())
        CURRENT = threading.Thread(target=run, daemon=True)
        CURRENT.start()


def log_job(line):
    secret = os.environ.get("GEMINI_API_KEY", "")
    if secret:
        line = line.replace(secret, "[redacted API key]")
    line = re.sub(r"AIza[A-Za-z0-9_-]{20,}", "[redacted API key]", line)
    with LOCK:
        j = read_json(JOB_FILE, {})
        j["log"] = (j.get("log", []) + [line[:400]])[-80:]
        if line.startswith("PROGRESS "):
            try:
                p = json.loads(line[9:])
                done = p.get("cached", 0) + p.get("completed", 0)
                j["progress"] = (f'{done}/{p.get("total", 0)} frames covered · '
                                 f'{p.get("cached", 0)} cached · {p.get("failed", 0)} failed')
            except ValueError:
                j["progress"] = line[:200]
        else:
            j["progress"] = line[:200]
        atomic_json(JOB_FILE, j)


def sync_frames():
    remote = bridge("status", timeout=15)
    entries = remote.get("frames", [])
    if not entries:
        return "Pi has no complete frames yet; check capture status"
    missing = []
    for e in entries:
        seq, size = int(e["seq"]), int(e["bytes"])
        if size <= 0:
            continue
        dest = FRAMES / f"{seq:06d}.jpg"
        if not dest.exists() or dest.stat().st_size != size:
            missing.append(seq)
    FRAMES.mkdir(exist_ok=True)
    log_job(f"{len(entries)} Pi frame rows; {len(missing)} images to copy")
    batches = [missing[i:i + 40] for i in range(0, len(missing), 40)] or [[]]
    copied = 0
    for batch in batches:
        if STOP.is_set():
            return f"Stopped after {copied} copied images"
        raw = bridge("export", ",".join(f"{x:06d}" for x in batch) if batch else "none", timeout=120, binary=True)
        if len(raw) > 30_000_000:
            raise RuntimeError("Pi export exceeded the 30 MB batch limit")
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
            members = archive.getmembers()
            names = [m.name for m in members]
            if len(names) != len(set(names)) or any(not m.isfile() or not re.fullmatch(r"(?:[0-9]{6}\.jpg|frames\.csv|manifest\.json)", m.name) or m.size > 10_000_000 for m in members):
                raise RuntimeError("Pi export contained an unsafe or oversized member")
            blobs = {m.name: archive.extractfile(m).read() for m in members}
        manifest = json.loads(blobs.get("manifest.json", b"{}").decode("utf-8"))
        expected = manifest.get("files", [])
        expected_seqs = {int(item["seq"]) for item in expected}
        if expected_seqs != set(batch):
            raise RuntimeError("Pi export omitted or added requested frames; retry sync")
        for item in expected:
            name = f'{int(item["seq"]):06d}.jpg'
            data = blobs.get(name)
            if data is None or len(data) != int(item["bytes"]) or hashlib.sha256(data).hexdigest() != item["sha256"]:
                raise RuntimeError(f"Pi export checksum mismatch for {name}")
            tmp = FRAMES / (name + ".tmp")
            tmp.write_bytes(data)
            os.replace(tmp, FRAMES / name)
            copied += 1
        if "frames.csv" in blobs:
            csv_bytes = blobs["frames.csv"]
            if hashlib.sha256(csv_bytes).hexdigest() != manifest.get("csv_sha256"):
                raise RuntimeError("Pi frames.csv checksum mismatch")
            decoded = csv_bytes.decode("utf-8")
            if set(("seq", "wall", "boottime", "bytes", "wb_locked")) - set(next(csv.reader(io.StringIO(decoded)), [])):
                raise RuntimeError("Pi frames.csv has an unexpected schema")
            local_csv = FRAMES / "frames.csv"
            if not local_csv.exists() or local_csv.read_bytes() != csv_bytes:
                tmp = FRAMES / "frames.csv.tmp"
                tmp.write_bytes(csv_bytes)
                os.replace(tmp, local_csv)
        log_job(f"Copied {copied}/{len(missing)} images")
    atomic_json(SYNC_FILE, {"last_success": now(), "copied": copied,
                            "remote_complete_frames": len(entries)})
    return f"Mirror current: {copied} new images copied"


def run_script(script, args=()):
    if script == "analyse.py" and not os.environ.get("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY is absent in the console process. Set it before starting the console.")
    command = [sys.executable, "-u", str(HERE / script), *args]
    if script == "analyse.py":
        command += ["--cancel-file", str(CANCEL_FILE)]
    child_env = os.environ.copy()
    child_env["TW_FRAMES"] = str(FRAMES)
    child_env.pop("TW_DEMO", None)
    p = subprocess.Popen(command, cwd=HERE,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                         encoding="utf-8", errors="replace", env=child_env)
    try:
        for line in p.stdout:
            log_job(line.rstrip())
            if STOP.is_set() and script != "analyse.py":
                p.terminate()
                break
        try:
            code = p.wait(timeout=8)
        except subprocess.TimeoutExpired:
            p.kill()
            code = p.wait()
        if STOP.is_set():
            return "Cancelled; rerun analysis to reuse saved readings"
        if code:
            raise RuntimeError(f"{script} exited with code {code}; see job log")
        return f"{script} completed"
    finally:
        if p.poll() is None:
            p.kill()


def roster_rows():
    if not ROSTER.exists():
        return []
    with ROSTER.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_roster(rows):
    if not isinstance(rows, list) or len(rows) > 3000:
        raise ValueError("Roster must be a list of at most 3000 rows")
    cols = ["day", "block", "from_ts", "slot", "dish", "is_veg"]
    seen = set()
    blocks = {}
    names = {}
    clean = []
    for r in rows:
        if not isinstance(r, dict):
            raise ValueError("Invalid roster row")
        day, block, at = str(r.get("day", "")), str(r.get("block", "")), str(r.get("from_ts", ""))
        try:
            datetime.strptime(day, "%Y-%m-%d")
            datetime.strptime(at, "%H:%M")
        except ValueError as e:
            raise ValueError("Use YYYY-MM-DD day and HH:MM start time") from e
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,20}", block):
            raise ValueError("Block name must be 1–20 letters, numbers, _ or -")
        slot = int(r.get("slot", 0))
        dish = str(r.get("dish", "")).strip()
        veg = str(r.get("is_veg", ""))
        if not 1 <= slot <= 99 or not dish or len(dish) > 80 or veg not in ("0", "1"):
            raise ValueError("Each row needs slot 1–99, a dish name, and vegetable 0 or 1")
        key = (day, block, slot)
        if key in seen:
            raise ValueError(f"Duplicate slot {slot} in {day} {block}")
        if dish.casefold() in names.setdefault((day, block), set()):
            raise ValueError(f"Duplicate dish {dish} in {day} {block}")
        seen.add(key)
        names[(day, block)].add(dish.casefold())
        blocks.setdefault((day, block), set()).add(at)
        clean.append({"day": day, "block": block, "from_ts": at, "slot": slot, "dish": dish, "is_veg": veg})
    if any(len(v) != 1 for v in blocks.values()):
        raise ValueError("All slots in a block must have the same start time")
    layout = read_json(HERE / "layout.json", {})
    expected_slots = {int(t["tray"]) for t in layout.get("trays", [])}
    if expected_slots:
        for day, block in blocks:
            slots = {r["slot"] for r in clean if r["day"] == day and r["block"] == block}
            if slots != expected_slots:
                raise ValueError(f"{day} {block} needs all {len(expected_slots)} layout slots: {sorted(expected_slots)}")
    for day in {r["day"] for r in clean}:
        ordered = sorted({(r["from_ts"], r["block"]) for r in clean if r["day"] == day})
        if len({x[0] for x in ordered}) != len(ordered):
            raise ValueError(f"Two blocks start at the same time on {day}")
        sets = [{r["slot"] for r in clean if r["day"] == day and r["block"] == b} for _, b in ordered]
        if len({tuple(sorted(s)) for s in sets}) > 1:
            raise ValueError(f"Each block on {day} must map the same slots")
    tmp = ROSTER.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        w.writerows(clean)
    os.replace(tmp, ROSTER)


def ensure_idle():
    if CURRENT and CURRENT.is_alive():
        raise ValueError("Wait for the current operation to finish before changing this setting")


def latest_draft():
    files = sorted(REPORTS.glob("*.html"), key=lambda p: p.stat().st_mtime, reverse=True) if REPORTS.exists() else []
    return files[0] if files else None


def analysis_outdated():
    daily = HERE / "daily.csv"
    if not daily.exists():
        return True
    written = daily.stat().st_mtime
    return any(p.exists() and p.stat().st_mtime > written + 0.01
               for p in (FRAMES, FRAMES / "frames.csv", ROSTER, HERE / "layout.json", HERE / "readings.csv"))


def analysis_estimate():
    p = FRAMES / "frames.csv"
    if not p.exists():
        return {"frames": 0, "cached": 0, "remaining": 0, "estimated_usd": 0}
    with p.open(newline="", encoding="utf-8") as f:
        frames = {int(r["seq"]) for r in csv.DictReader(f)
                  if int(r.get("bytes") or 0) > 0 and (FRAMES / f'{int(r["seq"]):06d}.jpg').exists()}
    layout = read_json(HERE / "layout.json", {})
    trays = len(layout.get("trays", []))
    counts = {}
    readings = HERE / "readings.csv"
    if readings.exists():
        with readings.open(newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("fill_raw") not in ("", None):
                    counts[int(r["seq"])] = counts.get(int(r["seq"]), 0) + 1
    cached = {seq for seq, n in counts.items() if trays and n >= trays}
    remaining = len(frames - cached)
    return {"frames": len(frames), "cached": len(frames & cached), "remaining": remaining,
            "estimated_usd": round(remaining * 0.001, 2)}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _valid_host(self):
        return self.headers.get("Host", "") in (f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}")

    def send(self, status, body, content_type="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8") if content_type.startswith("application/json") else body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; base-uri 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if not self._valid_host():
            return self.send(403, {"error": "Loopback Host required"})
        path = urlparse(self.path).path
        try:
            if path == "/":
                return self.send(200, (ASSETS / "index.html").read_text(encoding="utf-8").replace("__TOKEN__", TOKEN), "text/html; charset=utf-8")
            if path in ("/style.css", "/app.js"):
                return self.send(200, (ASSETS / path[1:]).read_bytes(), "text/css" if path.endswith("css") else "text/javascript")
            if path == "/api/overview":
                return self.send(200, overview())
            if path == "/api/latest":
                return self.send(200, bridge("latest", timeout=15))
            if path == "/api/roster":
                return self.send(200, {"rows": roster_rows()})
            if path == "/api/daily":
                p = HERE / "daily.csv"
                return self.send(200, {"rows": list(csv.DictReader(p.open(newline="", encoding="utf-8"))) if p.exists() else [],
                                       "outdated": analysis_outdated()})
            if path == "/api/analysis-estimate":
                return self.send(200, analysis_estimate())
            if path == "/api/frames":
                rows = []
                p = FRAMES / "frames.csv"
                if p.exists():
                    with p.open(newline="", encoding="utf-8") as f:
                        rows = list(csv.DictReader(f))[-150:]
                return self.send(200, {"rows": rows[::-1]})
            m = re.fullmatch(r"/api/frame/([0-9]{6})", path)
            if m:
                return self.send(200, (FRAMES / (m.group(1) + ".jpg")).read_bytes(), "image/jpeg")
            if path == "/api/draft":
                draft = latest_draft()
                return self.send(200, {"name": draft.name if draft else None, "html": draft.read_text(encoding="utf-8") if draft else None})
            if path == "/api/approved":
                return self.send(200, {"files": [p.name for p in sorted(APPROVED.glob("*.html"), reverse=True)] if APPROVED.exists() else []})
            m = re.fullmatch(r"/approved/([A-Za-z0-9_.-]+\.html)", path)
            if m:
                return self.send(200, (APPROVED / m.group(1)).read_text(encoding="utf-8"), "text/html; charset=utf-8")
            return self.send(404, {"error": "Not found"})
        except FileNotFoundError:
            return self.send(404, {"error": "File not found"})
        except Exception as e:
            return self.send(500, {"error": str(e)})

    def do_POST(self):
        if not self._valid_host() or self.headers.get("X-Traywatch-Token") != TOKEN:
            return self.send(403, {"error": "Local action token required"})
        origin = self.headers.get("Origin")
        if origin and origin not in (f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"):
            return self.send(403, {"error": "Invalid Origin"})
        try:
            n = int(self.headers.get("Content-Length", "0"))
            if n > 200_000 or n < 0:
                raise ValueError("Request is too large")
            data = json.loads(self.rfile.read(n) or b"{}")
            path = urlparse(self.path).path
            if path == "/api/settings":
                ensure_idle()
                c = {k: str(data.get(k, "")).strip() for k in CONFIG_DEFAULT}
                validate_config(c)
                atomic_json(CONFIG, c)
                return self.send(200, {"ok": True})
            if path == "/api/roster":
                ensure_idle()
                save_roster(data.get("rows"))
                return self.send(200, {"ok": True})
            if path == "/api/aim":
                return self.send(200, bridge("aim", timeout=25))
            if path == "/api/check-crop":
                ensure_idle()
                crop = str(data.get("crop", ""))
                if not re.fullmatch(r"\d+,\d+,[1-9]\d*,[1-9]\d*", crop):
                    raise ValueError("Crop must be x,y,width,height")
                result = bridge("check-crop", *crop.split(","), timeout=25)
                self.server.checked_crop = crop
                return self.send(200, result)
            if path == "/api/apply-crop":
                ensure_idle()
                crop = str(data.get("crop", ""))
                if crop != getattr(self.server, "checked_crop", None) or data.get("confirm") is not True:
                    raise ValueError("Review this exact cropped preview and confirm it contains no people before applying")
                self.server.checked_crop = None
                return self.send(200, bridge("apply-crop", *crop.split(","), timeout=30))
            if path == "/api/service":
                ensure_idle()
                action = data.get("action")
                if action not in ("start", "stop", "restart"):
                    raise ValueError("Invalid capture action")
                return self.send(200, bridge("service", action, timeout=30))
            if path == "/api/sync":
                start_job("sync", sync_frames)
                return self.send(202, {"ok": True})
            if path == "/api/analyse":
                if not FRAMES.exists() or not (FRAMES / "frames.csv").exists():
                    raise ValueError("Sync frames before analysing")
                start_job("analysis", lambda: run_script("analyse.py"))
                return self.send(202, {"ok": True})
            if path == "/api/report":
                if analysis_outdated():
                    raise ValueError("Frames or dish map changed since analysis. Run analysis again before drafting a report.")
                start_job("report", lambda: run_script("report.py", ["--no-llm"] if data.get("no_llm") else []))
                return self.send(202, {"ok": True})
            if path == "/api/cancel":
                STOP.set()
                CANCEL_FILE.write_text("cancel\n", encoding="utf-8")
                return self.send(200, {"ok": True})
            if path == "/api/approve":
                draft = latest_draft()
                if not draft or data.get("name") != draft.name or data.get("confirm") is not True:
                    raise ValueError("Review the current draft before approving")
                if analysis_outdated() or any(p.exists() and p.stat().st_mtime > draft.stat().st_mtime + 0.01
                                              for p in (HERE / "daily.csv", ROSTER, FRAMES / "frames.csv")):
                    raise ValueError("Source data changed after this draft. Create and review a new report.")
                APPROVED.mkdir(parents=True, exist_ok=True)
                source = (HERE / "daily.csv").read_bytes() if (HERE / "daily.csv").exists() else b""
                digest = hashlib.sha256(source + draft.read_bytes()).hexdigest()[:12]
                name = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + digest + ".html"
                dest = APPROVED / name
                with dest.open("x", encoding="utf-8") as f:
                    f.write(draft.read_text(encoding="utf-8"))
                return self.send(200, {"ok": True, "name": name})
            return self.send(404, {"error": "Not found"})
        except (ValueError, RuntimeError) as e:
            return self.send(400, {"error": str(e)})
        except Exception as e:
            return self.send(500, {"error": str(e)})


def main():
    port = int(os.environ.get("TW_CONSOLE_PORT", "8765"))
    old = read_json(JOB_FILE, {})
    if old.get("state") == "running":
        old.update(state="interrupted", ended=now(), progress="Console restarted; inspect saved files before rerunning")
        atomic_json(JOB_FILE, old)
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.checked_crop = None
    print(f"Tray Watch Console: http://127.0.0.1:{port}")
    print("Press Ctrl+C to stop the console. Pi capture continues independently.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
