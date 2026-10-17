"""Tests for privacy-safe RKLLM performance report aggregation."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from summarize_rkllm_runs import summarize, load

class RKLLMReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "run.json"
        self.sample = {
            "backend": "RKLLM C API", "model_file": "/models/a.rkllm",
            "max_new_tokens": 128, "context_tokens": 2048, "model_size_bytes": 10240,
            "initialized_ms": 150, "run_wall_ms": 500,
            "first_text_chunk_ms": 55, "text_chunks": 4, "output_utf8_bytes": 64,
            "finished_callback": True, "run_status": 0, "callback_error": False,
            "sdk_generate_tokens": 25, "sdk_generate_time_ms": 500,
            "sdk_tokens_per_sec": 50, "sdk_prefill_time_ms": 35,
            "sdk_peak_memory_mb": 900
        }
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.sample), encoding="utf8")

    def test_valid_report(self):
        s = summarize([self.path, self.path])
        self.assertEqual(s["runs"], 2)
        self.assertEqual(s["sdk_token_runs"], 2)
        self.assertEqual(s["statistics"]["sdk_tokens_per_sec"]["p95"], 50)
        self.assertFalse(s["hardware_verified"])

    def test_missing_sdk_telemetry_allowed(self):
        for key in ("sdk_generate_tokens", "sdk_generate_time_ms", "sdk_tokens_per_sec"):
            self.sample[key] = None
        self.save()
        self.assertIsNone(summarize([self.path])["statistics"]["sdk_tokens_per_sec"])
        with self.assertRaisesRegex(ValueError, "missing"):
            summarize([self.path], require_sdk_tokens=True)

    def test_reject_missing_finish(self):
        self.sample["finished_callback"] = False
        self.save()
        with self.assertRaisesRegex(ValueError, "callback"):
            load(self.path)

    def test_reject_inconsistent_rate(self):
        self.sample["sdk_tokens_per_sec"] = 80
        self.save()
        with self.assertRaisesRegex(ValueError, "inconsistent"):
            load(self.path)

    def test_reject_nan(self):
        self.path.write_text(self.path.read_text().replace("500", "NaN", 1))
        with self.assertRaisesRegex(ValueError, "invalid JSON"):
            load(self.path)

    def test_reject_generated_text_by_default(self):
        self.sample["generated_text"] = "private"
        self.save()
        with self.assertRaisesRegex(ValueError, "generated_text"):
            summarize([self.path])
        self.assertNotIn("private", json.dumps(summarize([self.path], allow_text=True)))

    def test_reject_different_models(self):
        other = self.path.parent / "second.json"
        other.write_text(json.dumps({**self.sample, "model_file": "/models/b.rkllm"}))
        with self.assertRaisesRegex(ValueError, "different model"):
            summarize([self.path, other])

    def test_reject_different_context(self):
        second = self.path.parent / "other.json"
        second.write_text(json.dumps({**self.sample, "context_tokens": 4096}))
        with self.assertRaisesRegex(ValueError, "inconsistent context_tokens"):
            summarize([self.path, second])

    def test_reject_invalid_config(self):
        self.sample["max_new_tokens"] = True
        self.save()
        with self.assertRaisesRegex(ValueError, "max_new_tokens"):
            load(self.path)

    def test_reject_duplicate_keys(self):
        self.path.write_text('{"backend":"RKLLM C API","backend":"fake"}')
        with self.assertRaisesRegex(ValueError, "duplicate"):
            load(self.path)

if __name__ == "__main__":
    unittest.main()
