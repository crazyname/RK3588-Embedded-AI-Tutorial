"""Dedicated executable-level tests of the C++ video pipeline with FAKE runtimes.

The executable must have been built by the CI workflow. This suite deliberately
checks CLI, missing-device and malformed inputs only: no simulated frame is
presented as a successful capture or NPU inference.
"""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]
BINARY = ROOT / "build/v4l2_rga_rknn_yolov8_mock"

class VideoNativeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not BINARY.is_file():
            raise unittest.SkipTest("Run after CI builds explicit V4L2/RGA/RKNN fake-runtime binary")

    def call(self, *args):
        return subprocess.run([str(BINARY), *map(str, args)],
                              capture_output=True, text=True, timeout=10)

    def test_help_does_not_open_device(self):
        self.assertEqual(self.call("--help").returncode, 0)

    def test_missing_parameters_rejected(self):
        self.assertNotEqual(self.call().returncode, 0)

    def test_nonexistent_camera_does_not_fake_frames(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            model = Path(d) / "fixture.rknn"
            model.write_bytes(b"FAKE MODEL FOR MOCK CI")
            result = self.call(model, "/dev/NO_CAMERA_FOR_RK3588_CI", "640", "480", "2", "0.25")
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('"detections":', result.stdout)

    def test_missing_model_rejected(self):
        result = self.call("/missing-model.rknn", "/dev/NO_CAMERA_FOR_RK3588_CI",
                           "640", "480", "2", "0.25")
        self.assertNotEqual(result.returncode, 0)

if __name__ == "__main__":
    unittest.main()
