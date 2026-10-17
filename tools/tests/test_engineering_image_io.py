"""Dedicated subprocess behavior tests for engineering conversion/preprocessing utilities."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable

def execute(script, *args):
    return subprocess.run([PY, str(ROOT / script), *map(str, args)],
                          capture_output=True, text=True, timeout=20)

class CompareOutputsTests(unittest.TestCase):
    def test_identical_and_numerically_different_arrays(self):
        import numpy as np
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            a, b = folder / "a.npz", folder / "b.npz"
            np.savez(a, output=np.array([[1., 2.]], dtype=np.float32))
            np.savez(b, output=np.array([[1., 2.]], dtype=np.float32))
            script = "examples/hardware/compare_outputs.py"
            self.assertEqual(execute(script, "--reference", a, "--candidate", b).returncode, 0)
            np.savez(b, output=np.array([[1., 20.]], dtype=np.float32))
            p = execute(script, "--reference", a, "--candidate", b)
            self.assertEqual(p.returncode, 1, p.stdout + p.stderr)

    def test_shape_and_tensor_name_mismatch(self):
        import numpy as np
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "a.npz", Path(d) / "b.npz"
            np.savez(a, logits=np.zeros((1, 2), np.float32))
            np.savez(b, logits=np.zeros((2, 2), np.float32))
            script = "examples/hardware/compare_outputs.py"
            self.assertEqual(execute(script, "--reference", a, "--candidate", b).returncode, 1)
            np.savez(b, other=np.zeros((1, 2), np.float32))
            self.assertNotEqual(execute(script, "--reference", a, "--candidate", b).returncode, 0)

    def test_missing_file_rejected(self):
        p = execute("examples/hardware/compare_outputs.py", "--reference", "/missing.npz", "--candidate", "/missing2.npz")
        self.assertNotEqual(p.returncode, 0)

class PrepareImageTests(unittest.TestCase):
    def test_rgb_bgr_nchw_raw_bytes(self):
        import numpy as np
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            src, out, raw = folder / "src.png", folder / "input.npy", folder / "input.bin"
            Image.new("RGB", (2, 2), (11, 22, 33)).save(src)
            p = execute("examples/hardware/prepare_image.py", "--image", src, "--output", out,
                        "--raw", raw, "--width", 2, "--height", 2, "--color", "BGR", "--layout", "NCHW")
            self.assertEqual(p.returncode, 0, p.stderr)
            array = np.load(out)
            self.assertEqual(array.shape, (1, 3, 2, 2))
            self.assertEqual([int(v) for v in array[0, :, 0, 0]], [33, 22, 11])
            self.assertEqual(raw.read_bytes(), array.tobytes())

    def test_normalization_and_invalid_std(self):
        import numpy as np
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            src, out = Path(d) / "x.png", Path(d) / "x.npy"
            Image.new("RGB", (1, 1), (20, 30, 40)).save(src)
            script = "examples/hardware/prepare_image.py"
            p = execute(script, "--image", src, "--output", out, "--width", 1, "--height", 1,
                        "--dtype", "float32", "--scale", "0.5", "--mean", "1,2,3", "--std", "3,1,1")
            self.assertEqual(p.returncode, 0, p.stderr)
            np.testing.assert_allclose(np.load(out)[0, 0, 0], [3, 13, 17], atol=1e-5)
            bad = execute(script, "--image", src, "--output", out, "--width", 1, "--height", 1,
                          "--std", "1,0,1")
            self.assertNotEqual(bad.returncode, 0)

    def test_uint8_normalization_rejected(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            src, out = Path(d) / "a.png", Path(d) / "a.npy"
            Image.new("RGB", (1, 1)).save(src)
            p = execute("examples/hardware/prepare_image.py", "--image", src, "--output", out,
                        "--width", 1, "--height", 1, "--scale", "0.5")
            self.assertNotEqual(p.returncode, 0)

if __name__ == "__main__":
    unittest.main()
