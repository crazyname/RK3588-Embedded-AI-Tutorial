"""Real OpenCV image preprocessing and negative-path checks (no NPU)."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
from prepare_yolov8_rgb import prepare

class PrepareYoloV8Tests(unittest.TestCase):
    def test_actual_bgr_to_rgb_black_padding(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            image=root/"source.png"
            bgr=np.full((480,640,3),[14,35,210],dtype=np.uint8)
            self.assertTrue(cv2.imwrite(str(image),bgr))
            output=root/"input.rgb"
            meta=root/"mapping.json"
            result=prepare(image,output,meta)
            self.assertEqual(output.stat().st_size,640*640*3)
            arr=np.frombuffer(output.read_bytes(),np.uint8).reshape((640,640,3))
            np.testing.assert_array_equal(arr[0,0],[0,0,0])
            np.testing.assert_array_equal(arr[80,0],[210,35,14])
            self.assertEqual(result["inverse_mapping"]["pad_y"],80)
            self.assertEqual(result["tensor_sha256"],hashlib.sha256(output.read_bytes()).hexdigest())
            self.assertEqual(json.loads(meta.read_text())["source_width"],640)
    def test_invalid_image_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with self.assertRaises(ValueError):
                prepare(root/"not-here.png",root/"output.raw",None)
            self.assertFalse((root/"output.raw").exists())
    def test_cli_generates_files_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            src=root/"frame.jpg"
            cv2.imwrite(str(src),np.full((32,48,3),100,dtype=np.uint8))
            run=subprocess.run([sys.executable,str(ROOT/"tools/prepare_yolov8_rgb.py"),
                    "--image",str(src),"--raw",str(root/"input.rgb"),
                    "--manifest",str(root/"mapping.json")],
                    capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual(json.loads(run.stdout)["source_height"],32)
            self.assertTrue((root/"input.rgb").exists())

if __name__=="__main__":
    unittest.main()
