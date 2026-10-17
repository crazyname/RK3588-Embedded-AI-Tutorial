"""Exercise three native RKNPU2 C++ executables with an explicitly FAKE SDK.

Use after downloading the official rknn_api.h into build/sdk-headers.
Mock success is only a code-path test, never evidence of NPU execution.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
HEADER = ROOT / "build/sdk-headers"
MOCK = ROOT / "examples/hardware/tests/mock_rknn_api.cpp"
SOURCES = {"classifier": "rknn_classify.cpp", "comparison": "rknn_compare_input_io.cpp",
           "zero_copy": "rknn_zero_copy.cpp"}

class NativeClassificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (HEADER / "rknn_api.h").is_file():
            raise unittest.SkipTest("Requires downloaded official header in build/sdk-headers")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        for label, src in SOURCES.items():
            binary = cls.root / label
            p = subprocess.run(["g++", "-std=c++17", "-O2", "-Wall", "-Wextra",
                                "-I" + str(HEADER), str(ROOT / "examples/hardware" / src),
                                str(MOCK), "-o", str(binary)],
                               capture_output=True, text=True, timeout=60)
            if p.returncode:
                raise AssertionError(f"{src}: {p.stderr}")
        cls.model = cls.root / "fake_model.rknn"
        cls.model.write_bytes(b"FAKE SDK FIXTURE")
        cls.good = cls.root / "good.raw"
        cls.good.write_bytes(bytes(range(48)))
        cls.bad = cls.root / "bad.raw"
        cls.bad.write_bytes(b"short")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_app(self, label, *args):
        return subprocess.run([str(self.root / label), *map(str, args)],
                              capture_output=True, text=True, timeout=10)

    def test_all_three_reject_missing_arguments(self):
        for name in SOURCES:
            with self.subTest(binary=name):
                self.assertNotEqual(self.run_app(name).returncode, 0)

    def test_all_three_reject_bad_input_size(self):
        for name in SOURCES:
            with self.subTest(binary=name):
                args = [self.model, self.bad]
                if name != "classifier":
                    args.append("2")
                p = self.run_app(name, *args)
                self.assertNotEqual(p.returncode, 0, p.stdout)

    def test_classifier_actual_fake_runtime_inference(self):
        p = self.run_app("classifier", self.model, self.good)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertTrue(p.stdout.strip())

    def test_zero_copy_actual_fake_runtime_binding(self):
        p = self.run_app("zero_copy", self.model, self.good, "2")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("output[0]=", p.stdout)
        self.assertIn("runs=2", p.stdout)
        self.assertIn("Input staging memcpy", p.stdout)

    def test_comparison_actual_fake_runtime_parity(self):
        p = self.run_app("comparison", self.model, self.good, "4", "1")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("allclose_atol_0.01_rtol_0.01=true", p.stdout)

    def test_zero_copy_invalid_run_count(self):
        p = self.run_app("zero_copy", self.model, self.good, "0")
        self.assertNotEqual(p.returncode, 0)

if __name__ == "__main__":
    unittest.main()
