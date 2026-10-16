"""Valid and invalid output records for the C++ V4L2/RGA/RKNN YOLOv8 log."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"boards/radxa-rock5b/tools"))
from validate_cpp_yolo_stream import assess

def row(frame=1):
    return {"frame":frame,"capture_ms":3.2,"rga_plus_cpu_letterbox_ms":2.4,
            "inference_and_decode_ms":17.7,
            "detections":[{"class_id":2,"score":0.94,"xyxy":[15,30,70,91]}]}

class StreamValidationTests(unittest.TestCase):
    def check(self,rows,**kwargs):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"video.jsonl"
            path.write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in rows)+"\n")
            return assess(path,640,480,**kwargs)
    def test_two_actual_records_and_p95(self):
        found=self.check([row(),row(2)],expected_frames=2,min_detections=2,
                         max_inference_p95=18)
        self.assertEqual(found["frames"],2)
        self.assertEqual(found["timing"]["inference_and_decode_ms"]["p95_ms"],17.7)
        self.assertFalse(found["hardware_verified"])
    def test_missing_and_nonsequential_frames_rejected(self):
        with self.assertRaisesRegex(ValueError,"consecutive"):
            self.check([row(2)])
        with self.assertRaisesRegex(ValueError,"Expected 3 frames"):
            self.check([row()],expected_frames=3)
    def test_out_of_frame_box_and_invalid_class(self):
        a=row();a["detections"][0]["xyxy"]=[-1,0,8,10]
        with self.assertRaisesRegex(ValueError,"outside expected range"):
            self.check([a])
        a=row();a["detections"][0]["class_id"]=100
        with self.assertRaisesRegex(ValueError,"COCO"):
            self.check([a])
    def test_unsorted_scores(self):
        a=row();a["detections"].append({"class_id":2,"score":1.0,"xyxy":[10,10,40,40]})
        with self.assertRaisesRegex(ValueError,"sorted"):
            self.check([a])
    def test_timing_nan_and_negative(self):
        a=row();a["capture_ms"]=float("nan")
        with self.assertRaisesRegex(ValueError,"Nonstandard JSON"):
            self.check([a])
        a=row();a["capture_ms"]=-10
        with self.assertRaisesRegex(ValueError,"outside expected range"):
            self.check([a])
    def test_minimum_detections_and_p95(self):
        with self.assertRaisesRegex(ValueError,"Too few"):
            self.check([row()],min_detections=2)
        with self.assertRaisesRegex(ValueError,"exceeds"):
            self.check([row()],max_inference_p95=1)
    def test_empty_file(self):
        with self.assertRaisesRegex(ValueError,"No frame"):
            self.check([])

if __name__=="__main__":
    unittest.main()
