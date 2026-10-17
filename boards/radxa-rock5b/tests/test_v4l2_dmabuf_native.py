"""Dedicated native V4L2 DMA-BUF probe failure/CLI tests without hardware.

Tests the actual compiled C++ executable; does not fake a successful DMA-BUF export.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "boards/radxa-rock5b/tools/v4l2_dmabuf_export_probe.cpp"

class DMABufProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.TemporaryDirectory()
        cls.binary = Path(cls.dir.name) / "probe"
        build = subprocess.run(["g++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-Werror",
                                str(SRC), "-o", str(cls.binary)], capture_output=True, text=True)
        if build.returncode:
            raise AssertionError(build.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.dir.cleanup()

    def invoke(self, *args):
        return subprocess.run([str(self.binary), *args], capture_output=True, text=True, timeout=5)

    def test_help_explicitly_limits_scope(self):
        p = self.invoke("--help")
        self.assertEqual(p.returncode, 0)
        self.assertIn("No streaming", p.stdout)

    def test_missing_camera_fails_without_false_success(self):
        p = self.invoke("/dev/this-camera-does-not-exist-rk3588-test")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("Cannot open camera", p.stderr)

    def test_missing_argument_rejected(self):
        self.assertEqual(self.invoke().returncode, 2)

    def test_regular_file_cannot_masquerade_as_capture_device(self):
        with tempfile.TemporaryDirectory() as d:
            pth = Path(d) / "not-a-camera"
            pth.write_bytes(b"not a V4L2 capture node")
            p = self.invoke(str(pth))
            self.assertNotEqual(p.returncode, 0)
            self.assertIn("VIDIOC_QUERYCAP", p.stderr)

if __name__ == "__main__":
    unittest.main()
