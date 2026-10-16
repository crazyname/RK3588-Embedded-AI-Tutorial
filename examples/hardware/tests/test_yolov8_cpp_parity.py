"""Cross-language *actual executable* regression against the Python YOLOv8 reference.

Requires a compiled C++ CPU decoder, set RK_YOLO_CPP_DECODER to its path.
Inputs are real FP32 tensor files; no NPU or fake prediction strings.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"boards/radxa-rock5b/apps"))
from yolov8_rknn_postprocess import decode as python_decode

class CrossLanguageParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        binary=os.environ.get("RK_YOLO_CPP_DECODER")
        if not binary:
            raise unittest.SkipTest("Set RK_YOLO_CPP_DECODER to compiled C++ CPU CLI")
        cls.binary=Path(binary).resolve()
        if not cls.binary.is_file():
            raise AssertionError("CPP decoder binary missing: "+str(cls.binary))

    def make_outputs(self,heads):
        outputs=[]
        spacing=heads//3
        for head,grid in enumerate((8,4,2)):
            box=np.full((1,64,grid,grid),-24,dtype=np.float32)
            for channel in (1,17,33,49):
                box[:,channel,:,:]=24
            cls=np.zeros((1,80,grid,grid),dtype=np.float32)
            if head==0:
                cls[0,2,4,4]=.93  # car
                cls[0,5,0,1]=.71  # bus
            if head==1:
                cls[0,2,1,1]=.82
            if head==2:
                cls[0,5,0,0]=.4
            outputs.extend([box,cls])
            if spacing==3:
                outputs.append(np.zeros((1,1,grid,grid),dtype=np.float32))
        return outputs

    def compare(self,heads,width,height,conf):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            outputs=self.make_outputs(heads)
            for i,t in enumerate(outputs):
                t.tofile(folder/f"out_{i}.f32")
            command=[str(self.binary),str(folder),str(heads),"8","4","2",
                     str(width),str(height),str(conf)]
            out=subprocess.run(command,text=True,capture_output=True,timeout=20)
            self.assertEqual(out.returncode,0,out.stderr)
            actual=json.loads(out.stdout)
            self.assertEqual(actual["backend"],"cpp-cpu-reference-not-npu")
            scale=min(640/width,640/height)
            nw=round(width*scale)
            nh=round(height*scale)
            meta={"source_wh":(width,height),"scale_x":nw/width,
                  "scale_y":nh/height,"pad_x":(640-nw)//2,"pad_y":(640-nh)//2}
            reference=python_decode(outputs,meta,size=640,num_classes=80,conf=conf)
            result=actual["detections"]
            self.assertEqual(len(result),len(reference))
            for got,expected in zip(result,reference):
                self.assertEqual(got["class_id"],expected["class_id"])
                self.assertAlmostEqual(got["score"],expected["score"],places=5)
                np.testing.assert_allclose(got["xyxy"],expected["xyxy"],
                                           rtol=1e-5,atol=1e-3)

    def test_nine_outputs_original_camera_ratio(self):
        self.compare(9,640,480,.25)
    def test_six_outputs_wide_camera(self):
        self.compare(6,1280,720,.25)
    def test_three_scale_no_candidates(self):
        self.compare(9,640,640,.99)
    def test_invalid_file_length_fails(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/"out_0.f32").write_bytes(b"broken")
            out=subprocess.run([str(self.binary),str(p),"9","8","4","2","640","480"],
                               text=True,capture_output=True,timeout=10)
            self.assertNotEqual(out.returncode,0)
            self.assertIn("byte length",out.stderr)
    def test_invalid_head_count_fails(self):
        with tempfile.TemporaryDirectory() as d:
            out=subprocess.run([str(self.binary),d,"7","8","4","2","640","480"],
                               text=True,capture_output=True,timeout=10)
            self.assertNotEqual(out.returncode,0)
            self.assertIn("Only 6 or 9",out.stderr)
    def test_nonfinite_class_scores_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            arrays=self.make_outputs(9)
            arrays[1][0,0,0,0]=float("nan")
            for i,array in enumerate(arrays):array.tofile(p/f"out_{i}.f32")
            run=subprocess.run([str(self.binary),str(p),"9","8","4","2","640","480"],
                               text=True,capture_output=True,timeout=10)
            self.assertNotEqual(run.returncode,0)
            self.assertIn("Non-finite class score",run.stderr)

if __name__=="__main__":
    unittest.main()
