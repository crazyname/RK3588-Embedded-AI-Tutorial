"""Dedicated tests of board camera capture and official YOLO launcher error/flow."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]

def load(filename, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

camera = load("usb_camera_check.py", "camera_dedicated")
official = load("run_official_yolov8.py", "official_dedicated")

class CaptureTests(unittest.TestCase):
    def test_capture_and_release(self):
        import numpy as np
        class FakeCamera:
            released = False
            def __init__(self, *_):
                self.i = 0
            def isOpened(self):
                return True
            def set(self, *_):
                return True
            def read(self):
                self.i += 1
                return True, np.zeros((3, 5, 3), np.uint8)
            def release(self):
                self.released = True
        fake_cv = types.SimpleNamespace(VideoCapture=FakeCamera, CAP_V4L2=200,
                                        CAP_ANY=0, CAP_PROP_FRAME_WIDTH=3, CAP_PROP_FRAME_HEIGHT=4)
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(sys.modules, {"cv2": fake_cv}), mock.patch.object(
                sys, "argv", ["camera", "--source", "0", "--frames", "3", "--save-json", str(Path(d) / "log.json")]):
            camera.main()
            report = json.loads((Path(d) / "log.json").read_text())
            self.assertEqual(report["frames"], 3)
            self.assertEqual(report["frame_shape"], [3, 5, 3])
            self.assertIn("NOT RK3588 NPU", report["note"])

    def test_failed_read_releases_camera(self):
        releases = []
        class BrokenCamera:
            def __init__(self, *_):
                pass
            def isOpened(self):
                return True
            def set(self, *_):
                pass
            def read(self):
                return False, None
            def release(self):
                releases.append(True)
        fake_cv = types.SimpleNamespace(VideoCapture=BrokenCamera, CAP_V4L2=200,
                                        CAP_ANY=0, CAP_PROP_FRAME_WIDTH=3, CAP_PROP_FRAME_HEIGHT=4)
        with mock.patch.dict(sys.modules, {"cv2": fake_cv}), mock.patch.object(
                sys, "argv", ["camera", "--frames", "3"]):
            with self.assertRaisesRegex(RuntimeError, "Camera read failed"):
                camera.main()
        self.assertEqual(releases, [True])

    def test_bad_capture_dimensions(self):
        with mock.patch.object(sys, "argv", ["camera", "--frames", "1"]):
            with self.assertRaises(SystemExit):
                camera.main()

class OfficialRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "python").mkdir()
        (self.root / "model").mkdir()
        (self.root / "python" / "yolov8.py").write_text("# test fixture\n")
        (self.root / "model" / "yolov8.rknn").write_bytes(b"test fixture")

    def test_dry_run_never_executes(self):
        with mock.patch.object(sys, "argv", ["launcher", "--example-root", str(self.root), "--dry-run"]), mock.patch.object(
                official.subprocess, "run", side_effect=AssertionError("must not execute")):
            official.main()

    def test_launch_uses_checked_vendor_path(self):
        with mock.patch.object(sys, "argv", ["launcher", "--example-root", str(self.root)]), mock.patch.object(
                official.subprocess, "run") as run:
            official.main()
            self.assertTrue(run.call_args.kwargs["check"])
            self.assertEqual(run.call_args.kwargs["cwd"], self.root / "python")

    def test_missing_image_directory_rejected(self):
        with self.assertRaises(FileNotFoundError):
            official.command_for(self.root, "python3", self.root / "missing", False)

if __name__ == "__main__":
    unittest.main()
