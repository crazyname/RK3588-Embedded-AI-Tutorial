"""Actual FP32 NPZ replay export tests with shape and type negative cases."""
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools"))
from export_yolov8_fp32 import export

def tensors(count=9,grids=(8,4,2)):
    per=count//3
    result={}
    for n in range(count):
        grid=grids[n//per]
        channels=64 if n%per==0 else 80 if n%per==1 else 1
        result[f"output_{n}"]=np.zeros((1,channels,grid,grid),dtype=np.float32)
    return result

class ExportTests(unittest.TestCase):
    def test_nine_tensors_export_all_files_correctly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            original=tensors(9)
            original["output_1"][0,2,4,4]=.93
            model=root/"board.npz"
            np.savez(model,**original)
            meta=export(model,root/"raw",(8,4,2))
            self.assertEqual(meta["output_tensors"],9)
            self.assertEqual(len(meta["source_sha256"]),64)
            self.assertTrue((root/"raw/manifest.json").is_file())
            actual=np.fromfile(root/"raw/out_1.f32",dtype="<f4")
            np.testing.assert_array_equal(actual.reshape(original["output_1"].shape),
                                          original["output_1"])
    def test_six_tensors_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            file=root/"six.npz";np.savez(file,**tensors(6))
            self.assertEqual(export(file,root/"out",(8,4,2))["output_tensors"],6)
    def test_integer_output_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            items=tensors()
            items["output_0"]=items["output_0"].astype(np.int8)
            file=root/"bad.npz";np.savez(file,**items)
            with self.assertRaisesRegex(ValueError,"float32"):
                export(file,root/"out",(8,4,2))
    def test_wrong_shape_and_missing_output_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            items=tensors()
            items["output_1"]=items["output_1"][:,:,:7,:]
            file=root/"bad.npz";np.savez(file,**items)
            with self.assertRaisesRegex(ValueError,"expected"):
                export(file,root/"out",(8,4,2))
            items=tensors()
            del items["output_6"]
            np.savez(file,**items)
            with self.assertRaisesRegex(ValueError,"exactly"):
                export(file,root/"out",(8,4,2))
    def test_nan_output_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            items=tensors()
            items["output_5"][0,0,0,0]=np.nan
            file=root/"bad.npz";np.savez(file,**items)
            with self.assertRaisesRegex(ValueError,"NaN"):
                export(file,root/"out",(8,4,2))

if __name__=="__main__":
    unittest.main()
