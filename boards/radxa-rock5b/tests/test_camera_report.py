"""Camera benchmark report structure/threshold tests (fixtures, NOT hardware results)."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"tools"/"validate_camera_report.py"
spec=importlib.util.spec_from_file_location("cam_report",SOURCE)
report=importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)

def fixture(digest):
    t={key:{"mean_ms":2.0,"p50_ms":1.0,"p95_ms":3.0,"max_ms":4.0}
       for key in report.STAGES}
    top=[{"class_index":1,"model_score":.9,"label":"one"},
         {"class_index":0,"model_score":.1,"label":"zero"}]
    summary={"backend":"RKNNLite (hardware when run with real board/SDK)",
             "processed_frames":2,"warmup_frames":1,"class_count":2,
             "input_dtype":"uint8","input_color":"RGB","no_frames_saved":True,
             "throughput_fps":18.5,"timing":t,"last_topk":top,
             "model_sha256":digest}
    rows=[{"frame":i,"topk":top,**{stage:1.0 for stage in report.STAGES}}
          for i in (1,2)]
    return summary,rows

class ReportTests(unittest.TestCase):
    def test_valid_report_and_exact_model_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            model=Path(tmp)/"my.rknn"
            model.write_bytes(b"NOT REAL NPU MODEL - checksum fixture")
            d=hashlib.sha256(model.read_bytes()).hexdigest()
            summary,rows=fixture(d)
            result=report.validate(summary,rows,model,min_fps=15,
                                   max_inference_p95=5)
            self.assertTrue(result["passed"])
            self.assertFalse(result["hardware_verified"])
            self.assertEqual(result["frame_count"],2)
    def test_threshold_failures(self):
        summary,rows=fixture("a"*64)
        with self.assertRaisesRegex(ValueError,"below"):
            report.validate(summary,rows,min_fps=20)
        with self.assertRaisesRegex(ValueError,"exceeds"):
            report.validate(summary,rows,max_inference_p95=1)
    def test_invalid_topk_and_nan(self):
        summary,rows=fixture("b"*64)
        summary["last_topk"][1]["model_score"]=1.1
        with self.assertRaisesRegex(ValueError,"sorted"):
            report.validate(summary,rows)
        summary,rows=fixture("b"*64)
        summary["throughput_fps"]=float("nan")
        with self.assertRaises(ValueError):
            report.validate(summary,rows)
    def test_rows_and_hash_mismatch(self):
        summary,rows=fixture("c"*64)
        with self.assertRaisesRegex(ValueError,"row count"):
            report.validate(summary,rows[:1])
        with tempfile.TemporaryDirectory() as tmp:
            model=Path(tmp)/"file.rknn"
            model.write_bytes(b"not matching recorded hash")
            with self.assertRaisesRegex(ValueError,"digest"):
                report.validate(summary,rows,model)
    def test_cli_roundtrip_with_fixture_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            model=folder/"model.rknn";model.write_bytes(b"test bytes")
            data,rows=fixture(hashlib.sha256(model.read_bytes()).hexdigest())
            summary=folder/"summary.json";summary.write_text(json.dumps(data))
            jsonl=folder/"frames.jsonl"
            jsonl.write_text("\n".join(json.dumps(row) for row in rows)+"\n")
            cmd=[sys.executable,str(SOURCE),"--summary",str(summary),
                 "--jsonl",str(jsonl),"--model",str(model)]
            out=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(out.returncode,0,out.stderr+out.stdout)
            self.assertTrue(json.loads(out.stdout)["passed"])
            out=subprocess.run(cmd+["--min-fps","200"],capture_output=True,text=True)
            self.assertNotEqual(out.returncode,0)

if __name__=="__main__":
    unittest.main()
