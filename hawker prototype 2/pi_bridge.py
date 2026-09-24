#!/usr/bin/env python3
"""Fixed-command SSH bridge for the laptop Tray Watch console.

JSON commands write one JSON object to stdout. ``export`` writes only tar bytes.
The capture daemon remains independent of this program and of the laptop.
"""

import base64
import csv
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
FRAMES = Path(os.environ.get("TW_FRAMES", HERE / "frames"))
CONFIG_DIR = Path.home() / ".config" / "traywatch"
CROP_ENV = CONFIG_DIR / "capture.env"
CHECK_META = CONFIG_DIR / "last-crop-check.json"
SERVICE = "traywatch.service"
COLS = ("seq", "wall", "boottime", "bytes", "wb_locked")
MAX_EXPORT_FILES = 100
MAX_EXPORT_BYTES = 50 * 1024 * 1024


class BridgeError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def json_out(value):
    print(json.dumps(value, separators=(",", ":")), flush=True)


def run(args, timeout=10):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                              check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BridgeError("command_failed", str(exc)) from exc


def crop_tuple(args):
    if len(args) != 4:
        raise BridgeError("invalid_crop", "crop requires X Y W H")
    try:
        x, y, w, h = (int(v) for v in args)
    except ValueError as exc:
        raise BridgeError("invalid_crop", "crop coordinates must be integers") from exc
    if min(x, y) < 0 or min(w, h) <= 0 or max(x, y, w, h) > 10000:
        raise BridgeError("invalid_crop", "crop origin must be nonnegative and size positive")
    return x, y, w, h


def crop_text(crop):
    return ",".join(map(str, crop))


def current_crop():
    try:
        lines = CROP_ENV.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return None
    values = [line[len("TW_CROP="):] for line in lines if line.startswith("TW_CROP=")]
    if len(values) != 1:
        raise BridgeError("invalid_config", "capture.env has no TW_CROP")
    return crop_tuple(values[0].split(","))


def configured_device():
    try:
        lines = CROP_ENV.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return "/dev/video0"
    values = [line[len("TW_DEV="):] for line in lines if line.startswith("TW_DEV=")]
    if not values:
        return "/dev/video0"
    if len(values) != 1 or not re.fullmatch(r"/dev/video[0-9]+", values[0]):
        raise BridgeError("invalid_config", "TW_DEV must name a /dev/videoN camera")
    return values[0]


def atomic_write(path, data):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".traywatch-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            os.fchmod(handle.fileno(), 0o600)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def write_crop(crop):
    atomic_write(CROP_ENV, ("TW_CROP=" + crop_text(crop) + "\nTW_DEV=" +
                            configured_device() + "\n").encode("ascii"))


def service_state():
    result = run(["systemctl", "show", SERVICE, "--property=ActiveState,SubState",
                  "--no-pager"])
    if result.returncode:
        return {"active": "unknown", "substate": "unknown", "error": result.stderr.strip()}
    values = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    return {"active": values.get("ActiveState", "unknown"),
            "substate": values.get("SubState", "unknown")}


def control_service(action):
    if action not in ("start", "stop", "restart"):
        raise BridgeError("invalid_action", "allowed actions: start, stop, restart")
    result = run(["sudo", "-n", "/usr/bin/systemctl", action, SERVICE], timeout=30)
    if result.returncode:
        raise BridgeError("service_permission_or_failure",
                          result.stderr.strip() or result.stdout.strip() or
                          "systemctl failed; check sudoers and service logs")
    return {"ok": True, "action": action, "service": service_state()}


def read_csv_snapshot():
    path = FRAMES / "frames.csv"
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return b"", []
    # capture.py flushes complete rows, but a concurrent read may end mid-append.
    if data and not data.endswith(b"\n"):
        data = data[:data.rfind(b"\n") + 1]
    try:
        text = data.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        if tuple(reader.fieldnames or ()) != COLS:
            raise BridgeError("invalid_csv", "frames.csv header is unexpected")
        rows = []
        seen_success = set()
        previous_seq = -1
        for row in reader:
            seq = int(row["seq"])
            size = int(row["bytes"])
            # capture.py reuses the same seq after a failed read (bytes=0), then
            # advances only when it has written a JPEG. Repeated failure rows are
            # therefore expected; two successful rows at one seq are not.
            if seq < previous_seq or size < 0 or seq in seen_success:
                raise ValueError("invalid sequence order or duplicate successful frame")
            if size > 0:
                seen_success.add(seq)
            previous_seq = seq
            rows.append({"seq": seq, "wall": row["wall"], "bytes": size,
                         "boottime": row["boottime"], "wb_locked": row["wb_locked"]})
    except (UnicodeError, ValueError, TypeError) as exc:
        raise BridgeError("invalid_csv", f"frames.csv is invalid: {exc}") from exc
    return data, rows


def frame_path(seq):
    return FRAMES / f"{seq:06d}.jpg"


def complete_frames(rows):
    complete = []
    for row in rows:
        if row["bytes"] <= 0:
            continue
        try:
            size = frame_path(row["seq"]).stat().st_size
        except FileNotFoundError:
            continue
        if size == row["bytes"]:
            complete.append({"seq": row["seq"], "bytes": size, "wall": row["wall"]})
    return complete


def status():
    errors = []
    try:
        crop = current_crop()
    except BridgeError as exc:
        crop = None
        errors.append({"code": exc.code, "message": str(exc)})
    try:
        _, rows = read_csv_snapshot()
        complete = complete_frames(rows)
    except BridgeError as exc:
        rows, complete = [], []
        errors.append({"code": exc.code, "message": str(exc)})
    clock = run(["timedatectl", "show", "-p", "NTPSynchronized", "-p", "Timezone",
                 "--no-pager"])
    vals = dict(line.split("=", 1) for line in clock.stdout.splitlines() if "=" in line)
    if clock.returncode:
        errors.append({"code": "clock_unknown", "message": clock.stderr.strip()})
    try:
        free = shutil.disk_usage(FRAMES if FRAMES.exists() else HERE).free
    except OSError:
        free = None
    return {"ok": True, "service": service_state(),
            "capture": {"crop": list(crop) if crop else None, "cadence_seconds": 120,
                        "latest": complete[-1] if complete else None,
                        "rows": rows[-20:]},
            "clock": {"synchronized": vals.get("NTPSynchronized") == "yes"
                      if "NTPSynchronized" in vals else None,
                      "timezone": vals.get("Timezone"), "now": time.strftime("%F %T")},
            "storage": {"free_bytes": free}, "frames": complete, "errors": errors}


def latest():
    _, rows = read_csv_snapshot()
    complete = complete_frames(rows)
    if not complete:
        raise BridgeError("no_frame", "no complete cropped frame has been captured")
    frame = complete[-1]
    if frame["bytes"] > 5 * 1024 * 1024:
        raise BridgeError("frame_too_large", "latest JPEG exceeds preview size limit")
    data = frame_path(frame["seq"]).read_bytes()
    if len(data) != frame["bytes"]:
        raise BridgeError("frame_changed", "latest JPEG changed while reading")
    return {"ok": True, "image": base64.b64encode(data).decode("ascii"),
            "seq": frame["seq"], "wall": frame["wall"]}


def camera_frame():
    try:
        import cv2
        import capture
    except ImportError as exc:
        raise BridgeError("camera_dependency", f"OpenCV/capture unavailable: {exc}") from exc
    capture.DEV = configured_device()
    camera = capture.open_cam()
    if camera is None:
        raise BridgeError("camera_busy_or_missing", "camera could not open; stop capture for preview if it is busy")
    try:
        ok, frame = camera.read()
        if not ok:
            raise BridgeError("camera_read_failed", "camera opened but returned no frame")
        return cv2, frame
    finally:
        camera.release()


def encode_jpeg(cv2, frame):
    ok, data = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not ok:
        raise BridgeError("image_encode_failed", "could not encode preview")
    h, w = frame.shape[:2]
    return {"ok": True, "image": base64.b64encode(data).decode("ascii"),
            "width": w, "height": h}


def aim():
    cv2, frame = camera_frame()
    h, w = frame.shape[:2]
    small = cv2.resize(frame, (240, max(1, round(240 * h / w))))
    small = cv2.GaussianBlur(small, (5, 5), 0)
    sh, sw = small.shape[:2]
    for i in range(1, 10):
        cv2.line(small, (sw * i // 10, 0), (sw * i // 10, sh), (0, 0, 255), 1)
        cv2.line(small, (0, sh * i // 10), (sw, sh * i // 10), (0, 0, 255), 1)
        cv2.putText(small, str(w * i // 10), (sw * i // 10 + 1, 8),
                    cv2.FONT_HERSHEY_PLAIN, 0.4, (0, 0, 255), 1)
        cv2.putText(small, str(h * i // 10), (1, sh * i // 10 - 1),
                    cv2.FONT_HERSHEY_PLAIN, 0.4, (0, 0, 255), 1)
    result = encode_jpeg(cv2, small)
    result.update({"sensor_width": w, "sensor_height": h})
    return result


def check_crop(crop):
    cv2, frame = camera_frame()
    h, w = frame.shape[:2]
    x, y, cw, ch = crop
    if x + cw > w or y + ch > h:
        raise BridgeError("crop_out_of_bounds", f"crop exceeds actual {w}x{h} camera frame")
    # This is the only image encoded. No uncropped image is encoded or written.
    result = encode_jpeg(cv2, frame[y:y + ch, x:x + cw])
    result["crop"] = list(crop)
    atomic_write(CHECK_META, json.dumps({"crop": list(crop),
                                         "checked_at": time.time()}).encode("ascii"))
    return result


def apply_crop(crop):
    try:
        checked = json.loads(CHECK_META.read_text(encoding="ascii"))
    except (FileNotFoundError, ValueError):
        raise BridgeError("crop_not_checked", "preview this crop before applying it")
    if checked.get("crop") != list(crop) or time.time() - checked.get("checked_at", 0) > 600:
        raise BridgeError("crop_not_checked", "matching crop preview must be less than ten minutes old")
    old_bytes = CROP_ENV.read_bytes() if CROP_ENV.exists() else None
    active = service_state().get("active") == "active"
    write_crop(crop)
    if active:
        try:
            control_service("restart")
        except BridgeError as exc:
            if old_bytes is not None:
                atomic_write(CROP_ENV, old_bytes)
                try:
                    control_service("restart")
                except BridgeError as restore_exc:
                    raise BridgeError("crop_restart_and_rollback_failed",
                                      f"new crop failed: {exc}; restoring previous crop also failed: {restore_exc}") from exc
            else:
                CROP_ENV.unlink(missing_ok=True)
            raise BridgeError("crop_restart_failed", f"previous crop configuration restored: {exc}") from exc
    CHECK_META.unlink(missing_ok=True)
    return {"ok": True, "crop": list(crop), "service": service_state(),
            "message": "crop applied and capture restarted" if active else
                       "crop applied; capture remains stopped"}


def export(selected):
    data, rows = read_csv_snapshot()
    available = {entry["seq"]: entry for entry in complete_frames(rows)}
    if selected == "none":
        seqs = []
    elif selected == "all":
        seqs = sorted(available)
    else:
        if not re.fullmatch(r"[0-9]+(?:,[0-9]+)*", selected):
            raise BridgeError("invalid_sequences", "export requires comma-separated sequences or all")
        seqs = [int(part) for part in selected.split(",")]
        if len(seqs) != len(set(seqs)):
            raise BridgeError("invalid_sequences", "duplicate requested sequence")
    if len(seqs) > MAX_EXPORT_FILES:
        raise BridgeError("export_too_large", f"limit is {MAX_EXPORT_FILES} frames per batch")
    missing = [seq for seq in seqs if seq not in available]
    if missing:
        raise BridgeError("incomplete_frames", f"not CSV-confirmed complete: {missing[:10]}")
    if sum(available[seq]["bytes"] for seq in seqs) > MAX_EXPORT_BYTES:
        raise BridgeError("export_too_large", f"limit is {MAX_EXPORT_BYTES} JPEG bytes per batch")
    blobs = {}
    files = []
    for seq in seqs:
        blob = frame_path(seq).read_bytes()
        if len(blob) != available[seq]["bytes"]:
            raise BridgeError("frame_changed", f"frame {seq} changed while exporting")
        blobs[seq] = blob
        files.append({"seq": seq, "bytes": len(blob),
                      "sha256": hashlib.sha256(blob).hexdigest()})
    manifest = json.dumps({"files": files, "csv_sha256": hashlib.sha256(data).hexdigest()},
                          separators=(",", ":")).encode("utf-8")
    with tarfile.open(fileobj=sys.stdout.buffer, mode="w|") as archive:
        for name, blob in [("manifest.json", manifest), ("frames.csv", data)] + [
                (f"{seq:06d}.jpg", blobs[seq]) for seq in seqs]:
            info = tarfile.TarInfo(name)
            info.size = len(blob)
            info.mode = 0o600
            archive.addfile(info, io.BytesIO(blob))


def main(argv):
    if not argv:
        raise BridgeError("usage", "command required: status, latest, aim, check-crop, apply-crop, service, export")
    command, *args = argv
    if command == "status" and not args:
        json_out(status())
    elif command == "latest" and not args:
        json_out(latest())
    elif command == "aim" and not args:
        json_out(aim())
    elif command == "check-crop":
        json_out(check_crop(crop_tuple(args)))
    elif command == "apply-crop":
        json_out(apply_crop(crop_tuple(args)))
    elif command == "service" and len(args) == 1:
        json_out(control_service(args[0]))
    elif command == "export" and len(args) == 1:
        export(args[0])
    else:
        raise BridgeError("usage", "invalid command or arguments")


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except BridgeError as exc:
        if len(sys.argv) > 1 and sys.argv[1] == "export":
            print(f"{exc.code}: {exc}", file=sys.stderr)
        else:
            json_out({"ok": False, "code": exc.code, "error": str(exc)})
        sys.exit(1)
