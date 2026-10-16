"""Deterministic PC tests using explicit fake camera and RKNNLite objects.

CI validates data conversion, error paths, resource cleanup and report contents.
It does NOT assert real RK3588 NPU results or USB-camera driver compatibility.
"""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"apps"))
spec=importlib.util.spec_from_file_location("camera_mobilenet_lite",
                                           ROOT/"apps"/"camera_mobilenet_lite.py")
app=importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

class FakeCapture:
    def __init__(self,frames):
        self.frames=list(frames)
        self.read_count=0
        self.released=False
    def read(self):
        self.read_count+=1
        if not self.frames:return False,None
        return True,self.frames.pop(0)
    def release(self):
        self.released=True

class FakeSDK:
    def __init__(self,fail=None):
        self.fail=fail
        self.infer_count=0
        self.released=False
        self.inputs=[]
    def load_rknn(self,model):
        return 8 if self.fail=="load" else 0
    def init_runtime(self):
        return 3 if self.fail=="init" else 0
    def inference(self,inputs):
        self.infer_count+=1
        self.inputs.append(inputs[0].copy())
        if self.fail=="infer":return None
        return [np.array([[.1,.9]],dtype=np.float32)]
    def release(self):
        self.released=True

def arguments(model,labels,folder):
    return SimpleNamespace(
        model=model,labels=labels,source="/dev/video7",frames=3,warmup=1,
        width=4,height=4,capture_width=8,capture_height=6,
        resize="stretch",topk=2,
        json=folder/"summary.json",jsonl=folder/"frames.jsonl",
        confirm_rgb_uint8_nhwc=True)

class CameraMobileNetTests(unittest.TestCase):
    def test_bgr_to_rgb_without_swap_error(self):
        bgr=np.zeros((2,3,3),dtype=np.uint8)
        bgr[:]=[10,20,240]
        tensor=app.prepare_bgr_frame(bgr,3,2,"stretch")
        self.assertEqual(tensor.dtype,np.uint8)
        self.assertEqual(tensor.shape,(2,3,3))
        self.assertEqual(tensor[0,0].tolist(),[240,20,10])
        self.assertTrue(tensor.flags.c_contiguous)
    def test_crop_and_invalid_frames(self):
        frame=np.full((8,4,3),[13,22,91],dtype=np.uint8)
        out=app.prepare_bgr_frame(frame,4,4,"center-crop")
        self.assertEqual(out.shape,(4,4,3))
        self.assertEqual(out[0,0].tolist(),[91,22,13])
        for bad in (np.zeros((2,2),dtype=np.uint8),
                    np.zeros((2,2,4),dtype=np.uint8),
                    np.zeros((2,2,3),dtype=np.float32)):
            with self.assertRaises(ValueError):
                app.prepare_bgr_frame(bad,4,4,"stretch")
    def test_statistics_median_p95(self):
        s=app.timing_summary([1,2,3,4,5,6,7,8,9,10])
        self.assertEqual(s["mean_ms"],5.5)
        self.assertEqual(s["p50_ms"],5.5)
        self.assertEqual(s["p95_ms"],10)
    def test_actual_pipeline_logic_mock_sdk(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            model=folder/"test.rknn";model.write_bytes(b"fixture, not a real model")
            labels=folder/"labels.txt";labels.write_text("zero\none\n")
            a=arguments(model,labels,folder)
            cap=FakeCapture([np.full((6,8,3),[4,8,12],dtype=np.uint8) for _ in range(4)])
            sdk=FakeSDK()
            result=app.execute(a,camera_factory=lambda *args:cap,sdk_factory=lambda:sdk)
            self.assertEqual(cap.read_count,4)
            self.assertEqual(sdk.infer_count,4)
            self.assertTrue(cap.released)
            self.assertTrue(sdk.released)
            self.assertEqual(len(sdk.inputs),4)
            self.assertEqual(sdk.inputs[0].shape,(4,4,3))
            self.assertEqual(sdk.inputs[0][0,0].tolist(),[12,8,4])
            self.assertEqual(result["processed_frames"],3)
            self.assertEqual(result["warmup_frames"],1)
            self.assertEqual(result["last_topk"][0]["label"],"one")
            self.assertTrue(result["no_frames_saved"])
            self.assertEqual(len(result["model_sha256"]),64)
            self.assertIn("p95_ms",result["timing"]["inference_ms"])
            self.assertEqual(len((folder/"frames.jsonl").read_text().splitlines()),3)
            self.assertEqual(json.loads((folder/"summary.json").read_text())["processed_frames"],3)
    def test_inference_failure_releases_devices(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            model=folder/"a.rknn";model.write_bytes(b"fixture")
            opts=arguments(model,None,folder)
            cap=FakeCapture([np.zeros((4,4,3),dtype=np.uint8)])
            sdk=FakeSDK(fail="infer")
            with self.assertRaises(RuntimeError):
                app.execute(opts,camera_factory=lambda *args:cap,
                            sdk_factory=lambda:sdk)
            self.assertTrue(cap.released)
            self.assertTrue(sdk.released)
            self.assertFalse((folder/"summary.json").exists())
    def test_runtime_load_failure_releases_devices(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            model=folder/"a.rknn";model.write_bytes(b"fixture")
            opts=arguments(model,None,folder)
            cap=FakeCapture([])
            sdk=FakeSDK(fail="load")
            with self.assertRaises(RuntimeError):
                app.execute(opts,camera_factory=lambda *args:cap,
                            sdk_factory=lambda:sdk)
            self.assertTrue(cap.released)
            self.assertTrue(sdk.released)
    def test_missing_model_and_wrong_labels(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            opts=arguments(folder/"no-model.rknn",None,folder)
            with self.assertRaises(FileNotFoundError):
                app.execute(opts,camera_factory=lambda *x:FakeCapture([]),
                            sdk_factory=FakeSDK)
            model=opts.model;model.write_bytes(b"fixture")
            labels=folder/"wrong.txt";labels.write_text("only one\n")
            opts.labels=labels
            cap=FakeCapture([np.zeros((6,8,3),dtype=np.uint8) for _ in range(4)])
            sdk=FakeSDK()
            with self.assertRaises(ValueError):
                app.execute(opts,camera_factory=lambda *x:cap,
                            sdk_factory=lambda:sdk)
            self.assertTrue(cap.released)
            self.assertTrue(sdk.released)

if __name__=="__main__":
    unittest.main()
