"""Focused tests for the laptop console's control and transfer boundaries."""
import csv
import hashlib
import importlib.util
import io
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
import tarfile
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("traywatch_console", HERE / "console.py")
console = importlib.util.module_from_spec(spec)
spec.loader.exec_module(console)


def archive(csv_data, files):
    manifest = {"files": [{"seq": seq, "bytes": len(blob),
                           "sha256": hashlib.sha256(blob).hexdigest()}
                          for seq, blob in files.items()],
                "csv_sha256": hashlib.sha256(csv_data).hexdigest()}
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w") as t:
        for name, blob in [("manifest.json", json.dumps(manifest).encode()),
                           ("frames.csv", csv_data)] + [(f"{s:06d}.jpg", b) for s, b in files.items()]:
            info = tarfile.TarInfo(name)
            info.size = len(blob)
            t.addfile(info, io.BytesIO(blob))
    return out.getvalue()


class ConsoleTests(unittest.TestCase):
    def test_roster_rejects_duplicate_and_incomplete_swap(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(console, "ROSTER", Path(tmp) / "dishes.csv"):
            a = {"day": "2026-09-24", "block": "am", "from_ts": "08:00", "slot": 1,
                 "dish": "kangkong", "is_veg": "1"}
            with self.assertRaisesRegex(ValueError, "Duplicate slot"):
                console.save_roster([a, a])
            with self.assertRaisesRegex(ValueError, "same slots"):
                console.save_roster([a, {**a, "block": "pm", "from_ts": "14:30", "slot": 2}])
            console.save_roster([a, {**a, "block": "pm", "from_ts": "14:30", "dish": "tofu"}])
            self.assertEqual(len(console.roster_rows()), 2)

    def test_sync_fills_sequence_hole_and_checks_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            frames = Path(tmp) / "frames"
            frames.mkdir()
            (frames / "000002.jpg").write_bytes(b"second")
            csv_data = ("seq,wall,boottime,bytes,wb_locked\n"
                        "1,2026-09-24 10:00:00,1,5,1\n"
                        "2,2026-09-24 10:02:00,2,6,1\n").encode()
            def bridge(*args, **kw):
                if args == ("status",):
                    return {"frames": [{"seq": 1, "bytes": 5}, {"seq": 2, "bytes": 6}]}
                self.assertEqual(args, ("export", "000001"))
                return archive(csv_data, {1: b"first"})
            with patch.object(console, "FRAMES", frames), patch.object(console, "JOB_FILE", Path(tmp) / "job.json"), patch.object(console, "SYNC_FILE", Path(tmp) / "sync.json"), patch.object(console, "bridge", side_effect=bridge):
                self.assertIn("1 new", console.sync_frames())
                self.assertEqual((frames / "000001.jpg").read_bytes(), b"first")
                self.assertEqual((frames / "000002.jpg").read_bytes(), b"second")
                self.assertEqual((frames / "frames.csv").read_bytes(), csv_data)

    def test_http_rejects_mutation_without_token(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), console.Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/api/service"
            req = Request(url, data=b'{}', method="POST")
            with self.assertRaises(HTTPError) as got:
                urlopen(req, timeout=3)
            self.assertEqual(got.exception.code, 403)
        finally:
            server.shutdown()
            server.server_close()

    def test_crop_preview_and_apply_use_fixed_pi_arguments(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), console.Handler)
        server.checked_crop = None
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        calls = []
        def fake_bridge(*args, **kw):
            calls.append(args)
            return {"ok": True, "crop": [1, 2, 300, 400], "image": "AA=="}
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            def post(path, body):
                req = Request(base + path, data=json.dumps(body).encode(), method="POST",
                              headers={"Content-Type": "application/json",
                                       "X-Traywatch-Token": console.TOKEN})
                return json.load(urlopen(req, timeout=3))
            with patch.object(console, "bridge", side_effect=fake_bridge):
                with self.assertRaises(HTTPError) as got:
                    post("/api/apply-crop", {"crop": "1,2,300,400", "confirm": True})
                self.assertEqual(got.exception.code, 400)
                post("/api/check-crop", {"crop": "1,2,300,400"})
                post("/api/apply-crop", {"crop": "1,2,300,400", "confirm": True})
            self.assertEqual(calls, [("check-crop", "1", "2", "300", "400"),
                                     ("apply-crop", "1", "2", "300", "400")])
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
