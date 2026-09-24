"""Pi bridge contract tests that run without systemd, SSH, or a camera."""

import base64
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pi_bridge as bridge


class BridgeContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.frames = root / "frames"
        self.frames.mkdir()
        self.patches = [patch.object(bridge, "FRAMES", self.frames),
                        patch.object(bridge, "CONFIG_DIR", root / "config"),
                        patch.object(bridge, "CROP_ENV", root / "config" / "capture.env"),
                        patch.object(bridge, "CHECK_META", root / "config" / "last-crop-check.json")]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def write_csv(self):
        (self.frames / "frames.csv").write_text(
            "seq,wall,boottime,bytes,wb_locked\n"
            "0,2026-09-24 08:00:00,10,0,1\n"
            "0,2026-09-24 08:02:00,130,4,1\n"
            "1,2026-09-24 08:04:00,250,5,1\n", encoding="utf-8")
        (self.frames / "000000.jpg").write_bytes(b"JPEG")
        (self.frames / "000001.jpg").write_bytes(b"bad")

    def test_repeated_failure_sequence_and_incomplete_frame(self):
        self.write_csv()
        _, rows = bridge.read_csv_snapshot()
        self.assertEqual([row["seq"] for row in rows], [0, 0, 1])
        self.assertEqual([row["seq"] for row in bridge.complete_frames(rows)], [0])
        self.assertEqual(bridge.latest()["seq"], 0)
        self.assertEqual(base64.b64decode(bridge.latest()["image"]), b"JPEG")

    def test_export_manifest_and_csv_only(self):
        self.write_csv()
        for selection, expected in [("0", ["000000.jpg"]), ("none", [])]:
            sink = io.BytesIO()
            with patch.object(bridge.sys, "stdout", SimpleNamespace(buffer=sink)):
                bridge.export(selection)
            sink.seek(0)
            with tarfile.open(fileobj=sink, mode="r:") as archive:
                names = archive.getnames()
                self.assertEqual(names, ["manifest.json", "frames.csv"] + expected)
                manifest = json.load(archive.extractfile("manifest.json"))
                self.assertEqual([f["seq"] for f in manifest["files"]],
                                 [0] if selection == "0" else [])
        with self.assertRaises(bridge.BridgeError):
            bridge.export("1")  # CSV says 5 bytes, JPEG has only 3.

    def test_crop_preview_is_only_the_selected_rectangle(self):
        import cv2
        import numpy as np

        frame = np.zeros((100, 200, 3), dtype=np.uint8)
        frame[:10, :10] = 255  # outside the requested crop
        with patch.object(bridge, "camera_frame", return_value=(cv2, frame)):
            result = bridge.check_crop((50, 20, 40, 30))
        decoded = cv2.imdecode(np.frombuffer(base64.b64decode(result["image"]), np.uint8),
                               cv2.IMREAD_COLOR)
        self.assertEqual(decoded.shape[:2], (30, 40))
        self.assertEqual(int(decoded.max()), 0)
        self.assertEqual(json.loads(bridge.CHECK_META.read_text())["crop"], [50, 20, 40, 30])
        self.assertFalse((self.frames / "check.jpg").exists())

    def test_apply_requires_recent_matching_preview_and_preserves_stopped_service(self):
        import time

        bridge.CONFIG_DIR.mkdir()
        bridge.CROP_ENV.write_text("TW_CROP=1,2,10,10\nTW_DEV=/dev/video2\n")
        with patch.object(bridge, "service_state", return_value={"active": "inactive"}):
            with self.assertRaises(bridge.BridgeError):
                bridge.apply_crop((5, 6, 20, 20))
            bridge.CHECK_META.write_text(json.dumps({"crop": [5, 6, 20, 20],
                                                     "checked_at": time.time()}))
            result = bridge.apply_crop((5, 6, 20, 20))
        self.assertEqual(result["service"]["active"], "inactive")
        self.assertEqual(bridge.CROP_ENV.read_text(),
                         "TW_CROP=5,6,20,20\nTW_DEV=/dev/video2\n")
        self.assertFalse(bridge.CHECK_META.exists())


if __name__ == "__main__":
    unittest.main()
