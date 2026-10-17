"""Regression tests for the engineering source/runbook/acceptance audit."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_engineering import audit, ROOT

class EngineeringAuditTests(unittest.TestCase):
    def test_repo_has_no_unmapped_engineering_source(self):
        projects, covered, expected, problems = audit()
        self.assertGreaterEqual(projects, 17)
        self.assertGreaterEqual(covered, expected)
        self.assertEqual(problems, [])

    def test_missing_runbook_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test-manifest.json"
            data = json.loads((ROOT / "engineering/manifest.json").read_text(encoding="utf-8"))
            data["projects"][0]["experiment"] = "engineering/not-here.md"
            path.write_text(json.dumps(data), encoding="utf8")
            *_, problems = audit(ROOT, path)
            self.assertTrue(any("invalid runbook" in item for item in problems))

    def test_missing_test_is_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test-manifest.json"
            data = json.loads((ROOT / "engineering/manifest.json").read_text(encoding="utf-8"))
            data["projects"][0]["tests"] = ["boards/radxa-rock5b/tests/missing_file.py"]
            path.write_text(json.dumps(data), encoding="utf8")
            *_, problems = audit(ROOT, path)
            self.assertTrue(any("missing test" in item for item in problems))

    def test_unmapped_source_is_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test-manifest.json"
            data = json.loads((ROOT / "engineering/manifest.json").read_text(encoding="utf-8"))
            data["projects"] = data["projects"][1:]
            path.write_text(json.dumps(data), encoding="utf8")
            *_, problems = audit(ROOT, path)
            self.assertTrue(any("unmapped engineering source" in item for item in problems))

if __name__ == "__main__":
    unittest.main()
