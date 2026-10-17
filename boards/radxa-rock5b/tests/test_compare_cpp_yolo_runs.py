"""Offline tests for comparable C++ YOLOv8 benchmark runs."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "compare_cpp_yolo_runs.py"
import sys
sys.path.insert(0, str(SCRIPT.parent))
from compare_cpp_yolo_runs import compare, load_manifest

class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.log1 = self.root / "a.jsonl"
        self.log2 = self.root / "b.jsonl"
        self.meta1 = self.root / "a.json"
        self.meta2 = self.root / "b.json"
        for path, latency in ((self.log1, 10.0), (self.log2, 12.0)):
            rows = [{"frame": idx, "capture_ms": 2.0, "rga_plus_cpu_letterbox_ms": 3.0,
                     "inference_and_decode_ms": latency,
                     "detections": [{"class_id": 0, "score": 0.9, "xyxy": [1, 2, 30, 40]}]}
                    for idx in range(1, 4)]
            path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf8")
        self.make_meta(self.log1, self.meta1)
        self.make_meta(self.log2, self.meta2)

    def make_meta(self, log, dest, **overrides):
        meta = {"board": "ROCK 5B rev X 16GB", "os_image": "test-image",
                "kernel": "test-kernel", "npu_driver": "test-driver",
                "rknn_runtime": "test-runtime", "rga_version": "test-rga",
                "model_sha256": "a" * 64, "model_contract": "optimized 640 rgb uint8",
                "camera_format": "YUYV", "camera_width": 640,
                "camera_height": 480, "camera_fps": 30,
                "pipeline": "v4l2-rga-rknn-cpp", "measurement_protocol": "3 frames no warmup",
                "evidence_type": "synthetic",
                "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest()}
        meta.update(overrides)
        dest.write_text(json.dumps(meta), encoding="utf8")

    def test_comparable_latency(self):
        report = compare(self.log1, self.meta1, self.log2, self.meta2)
        self.assertTrue(report["comparison_valid"])
        self.assertEqual(report["inference_decode_p95_delta_ms"], 2)
        self.assertEqual(report["inference_decode_p95_delta_percent"], 20)
        self.assertFalse(report["hardware_verified"])

    def test_changed_model_rejected(self):
        self.make_meta(self.log2, self.meta2, model_sha256="b" * 64)
        with self.assertRaisesRegex(ValueError, "model_sha256"):
            compare(self.log1, self.meta1, self.log2, self.meta2)

    def test_mismatch_only_diagnostics(self):
        self.make_meta(self.log2, self.meta2, camera_fps=60)
        report = compare(self.log1, self.meta1, self.log2, self.meta2, True)
        self.assertFalse(report["comparison_valid"])
        self.assertIn("camera_fps", report["config_differences"])

    def test_tampered_log_rejected(self):
        self.log2.write_text(self.log2.read_text() + "\n", encoding="utf8")
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            compare(self.log1, self.meta1, self.log2, self.meta2)

    def test_missing_metadata_rejected(self):
        self.make_meta(self.log2, self.meta2, npu_driver="unknown")
        with self.assertRaisesRegex(ValueError, "npu_driver"):
            load_manifest(self.meta2)

    def test_duplicate_manifest_key_rejected(self):
        self.meta2.write_text('{"board":"X","board":"Y"}', encoding="utf8")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            load_manifest(self.meta2)

    def test_invalid_record_rejected(self):
        rows = self.log2.read_text().splitlines()
        row = json.loads(rows[0])
        row["detections"][0]["xyxy"] = [0, 0, 900, 480]
        rows[0] = json.dumps(row)
        self.log2.write_text("\n".join(rows) + "\n", encoding="utf8")
        self.make_meta(self.log2, self.meta2)
        with self.assertRaisesRegex(ValueError, "inside original camera frame"):
            compare(self.log1, self.meta1, self.log2, self.meta2)

if __name__ == "__main__":
    unittest.main()
