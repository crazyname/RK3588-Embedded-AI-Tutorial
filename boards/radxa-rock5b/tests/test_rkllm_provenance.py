"""Offline tests for RKLLM experiment provenance hashing."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from rkllm_provenance import create, verify

class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.model = root / "model.rkllm"
        self.prompt = root / "prompt.txt"
        self.report = root / "report.json"
        self.manifest = root / "manifest.json"
        self.model.write_bytes(b"mock model bytes")
        self.prompt.write_text("test input", encoding="utf-8")
        self.data = {"backend": "RKLLM C API", "run_status": 0,
                     "finished_callback": True, "callback_error": False,
                     "context_tokens": 2048, "max_new_tokens": 128,
                     "model_size_bytes": self.model.stat().st_size}
        self.write_report()

    def write_report(self):
        self.report.write_text(json.dumps(self.data), encoding="utf-8")

    def save_manifest(self):
        self.manifest.write_text(json.dumps(create(self.report, self.model, self.prompt)))

    def test_create_and_verify(self):
        self.save_manifest()
        result = verify(self.manifest, self.report, self.model, self.prompt)
        self.assertEqual(len(result["model_sha256"]), 64)
        self.assertFalse(result["hardware_verified"])
        self.assertNotIn("test input", str(result))

    def test_changed_prompt_rejected(self):
        self.save_manifest()
        self.prompt.write_text("different input", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "prompt_sha256"):
            verify(self.manifest, self.report, self.model, self.prompt)

    def test_changed_model_same_size_rejected(self):
        self.save_manifest()
        self.model.write_bytes(b"Mock model bytes")
        with self.assertRaisesRegex(ValueError, "model_sha256"):
            verify(self.manifest, self.report, self.model, self.prompt)

    def test_changed_report_rejected(self):
        self.save_manifest()
        self.data["context_tokens"] = 4096
        self.write_report()
        with self.assertRaisesRegex(ValueError, "report_sha256"):
            verify(self.manifest, self.report, self.model, self.prompt)

    def test_wrong_model_size_rejected(self):
        self.data["model_size_bytes"] = 1
        self.write_report()
        with self.assertRaisesRegex(ValueError, "size"):
            create(self.report, self.model, self.prompt)

    def test_failed_run_rejected(self):
        self.data["run_status"] = 1
        self.write_report()
        with self.assertRaisesRegex(ValueError, "failed"):
            create(self.report, self.model, self.prompt)

    def test_duplicate_report_keys_rejected(self):
        self.report.write_text('{"backend":"RKLLM C API","backend":"fake"}')
        with self.assertRaisesRegex(ValueError, "duplicate"):
            create(self.report, self.model, self.prompt)

    def test_tampered_manifest_rejected(self):
        self.save_manifest()
        doc = json.loads(self.manifest.read_text())
        doc["model_sha256"] = "0" * 64
        self.manifest.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError, "model_sha256"):
            verify(self.manifest, self.report, self.model, self.prompt)

if __name__ == "__main__":
    unittest.main()
