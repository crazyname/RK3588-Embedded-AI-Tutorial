"""Real tensor math fixtures for Rockchip Model Zoo optimized YOLOv8.
All RKNNLite/USB camera calls below are explicit fakes; no hardware claim.
"""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
import numpy as np

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/"apps"))
import yolov8_rknn_postprocess as post
import camera_yolov8_lite as app

def model_outputs(count=9,score=.93):
    """3 heads with actual [1,64,H,W] DFL logits; 80 class channels, 1 sum."""
    outputs=[]
    for j,grid in enumerate((8,4,2)):
        box=np.full((1,64,grid,grid),-20.0,dtype=np.float32)
        box[:,[1,17,33,49],:,:]=20.0  # ltrb all one grid cell
        cls=np.zeros((1,80,grid,grid),dtype=np.float32)
        if j==0:cls[0,2,4,4]=score  # class 2, cell 4,4
        outputs.extend([box,cls])
        if count==9:outputs.append(np.zeros((1,1,grid,grid),dtype=np.float32))
    return outputs

class PostprocessTests(unittest.TestCase):
    def test_true_dfl_expected_value(self):
        tensor=np.full((1,64,1,1),-30,dtype=np.float32)
        tensor[:,[1,17,33,49]]=30
        distances=post.dfl(tensor)
        self.assertEqual(distances.shape,(1,4,1,1))
        np.testing.assert_allclose(distances[0,:,0,0],[1,1,1,1],atol=1e-5)
    def test_letterbox_bgr_rgb_black_padding(self):
        import cv2
        frame=np.full((480,640,3),[13,24,201],dtype=np.uint8)
        prepared,meta=post.letterbox(frame)
        self.assertEqual(prepared.shape,(640,640,3))
        np.testing.assert_array_equal(prepared[0,0],[0,0,0])
        np.testing.assert_array_equal(prepared[100,100],[201,24,13])
        self.assertEqual(meta["pad_y"],80)
        self.assertEqual(meta["source_wh"],(640,480))
        self.assertEqual(meta["scale_x"],1)
    def test_9_output_decode_original_xyxy(self):
        meta={"source_wh":(640,480),"scale_x":1.,"scale_y":1.,
              "pad_x":0,"pad_y":80}
        boxes=post.decode(model_outputs(9),meta,size=640,conf=.25)
        self.assertEqual(len(boxes),1)
        self.assertEqual(boxes[0]["class_id"],2)
        self.assertAlmostEqual(boxes[0]["score"],.93,places=5)
        np.testing.assert_allclose(boxes[0]["xyxy"],[280,200,440,360],atol=1e-2)
    def test_6_output_without_conf_sum(self):
        meta={"source_wh":(640,640),"scale_x":1.,"scale_y":1.,"pad_x":0,"pad_y":0}
        self.assertEqual(len(post.decode(model_outputs(6),meta)),1)
        self.assertEqual(post.decode(model_outputs(9,score=.1),meta),[])
    def test_unsupported_ultralytics_layout_rejected(self):
        meta={"source_wh":(640,640),"scale_x":1.,"scale_y":1.,"pad_x":0,"pad_y":0}
        with self.assertRaisesRegex(ValueError,"Expected 6 or 9"):
            post.decode([np.zeros((1,84,8400),dtype=np.float32)],meta)
        values=model_outputs()
        values[0]=values[0].astype(np.int8)
        with self.assertRaisesRegex(ValueError,"dequantized float"):
            post.decode(values,meta)
        values=model_outputs()
        values[1]=np.zeros((1,79,8,8),dtype=np.float32)
        with self.assertRaisesRegex(ValueError,"class channels"):
            post.decode(values,meta)
        values=model_outputs()
        values[2]=np.zeros((1,2,8,8),dtype=np.float32)
        with self.assertRaisesRegex(ValueError,"Auxiliary"):
            post.decode(values,meta)
    def test_class_aware_nms(self):
        boxes=np.asarray([[0,0,10,10],[1,1,9,9],[30,30,40,40]],dtype=np.float32)
        self.assertEqual(post.nms(boxes,[.9,.8,.7],.45,10).tolist(),[0,2])
        self.assertEqual(post.nms(boxes,[.9,.8,.7],.45,1).tolist(),[0])
    def test_annotations_actual_cv2(self):
        import cv2
        frame=np.zeros((100,100,3),dtype=np.uint8)
        d=[{"class_id":2,"score":.91,"xyxy":[10,20,50,70]}]
        image=post.draw_detections(frame,d,app.read_labels(app.DEFAULT_LABELS))
        self.assertTrue(np.any(image!=frame))
        self.assertTrue(np.all(frame==0))

class FakeCamera:
    def __init__(self,count):
        self.frames=count
        self.released=False
    def read(self):
        if not self.frames:return False,None
        self.frames-=1
        return True,np.full((480,640,3),[20,40,60],dtype=np.uint8)
    def release(self):self.released=True

class FakeNPU:
    def __init__(self,fail=None):
        self.fail=fail
        self.released=False
        self.inputs=[]
    def load_rknn(self,path):return 9 if self.fail=="load" else 0
    def init_runtime(self):return 7 if self.fail=="init" else 0
    def inference(self,inputs):
        self.inputs.append(inputs[0].copy())
        if self.fail=="infer":return None
        return model_outputs()
    def release(self):self.released=True

def fake_options(folder):
    model=folder/"fake.rknn"
    model.write_bytes(b"Only for mock SDK control-flow tests")
    return types.SimpleNamespace(model=model,labels=app.DEFAULT_LABELS,source="/dev/video7",
            capture_width=640,capture_height=480,size=640,frames=2,warmup=1,
            conf=.25,iou=.45,max_det=10,
            summary=folder/"report.json",jsonl=folder/"frames.jsonl",
            output_image=None,output_video=None,view=False,
            confirm_optimized_yolov8=True)

class PipelineTests(unittest.TestCase):
    def test_mock_camera_and_sdk_dataflow(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            args=fake_options(root)
            camera=FakeCamera(3)
            sdk=FakeNPU()
            report=app.execute(args,camera_factory=lambda *a:camera,rknn_factory=lambda:sdk)
            self.assertTrue(camera.released and sdk.released)
            self.assertEqual(len(sdk.inputs),3)
            self.assertEqual(sdk.inputs[0].shape,(640,640,3))
            np.testing.assert_array_equal(sdk.inputs[0][100,100],[60,40,20])
            self.assertEqual(report["measured_frames"],2)
            self.assertEqual(report["total_detections"],2)
            self.assertEqual(report["last_detections"][0]["label"],"car")
            self.assertEqual(len(report["model_sha256"]),64)
            self.assertIn("p95_ms",report["timing"]["postprocess_ms"])
            self.assertEqual(len((root/"frames.jsonl").read_text().splitlines()),2)
            self.assertEqual(json.loads((root/"report.json").read_text())["measured_frames"],2)
    def test_fake_sdk_failure_clean_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);a=fake_options(root);camera=FakeCamera(3);sdk=FakeNPU("infer")
            with self.assertRaisesRegex(ValueError,"Expected 6 or 9"):
                app.execute(a,camera_factory=lambda *x:camera,rknn_factory=lambda:sdk)
            self.assertTrue(camera.released and sdk.released)
            self.assertFalse((root/"report.json").exists())
    def test_missing_camera_frame_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);a=fake_options(root);cam=FakeCamera(1);sdk=FakeNPU()
            with self.assertRaisesRegex(RuntimeError,"frame read failed"):
                app.execute(a,camera_factory=lambda *x:cam,rknn_factory=lambda:sdk)
            self.assertTrue(cam.released and sdk.released)
    def test_wrong_model_protocol_and_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);a=fake_options(root)
            a.confirm_optimized_yolov8=False
            with self.assertRaisesRegex(ValueError,"confirm"):
                app.execute(a)
            a.confirm_optimized_yolov8=True;a.size=320
            with self.assertRaisesRegex(ValueError,"640x640"):
                app.execute(a)
    def test_mock_annotated_image_saved_opt_in(self):
        import cv2
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);a=fake_options(root)
            a.output_image=root/"annotated.png";a.frames=1;a.warmup=0
            cam=FakeCamera(1);sdk=FakeNPU()
            result=app.execute(a,camera_factory=lambda *x:cam,rknn_factory=lambda:sdk)
            self.assertTrue(a.output_image.is_file())
            annotated=cv2.imread(str(a.output_image))
            self.assertEqual(annotated.shape,(480,640,3))
            self.assertEqual(result["total_detections"],1)

if __name__=="__main__":
    unittest.main()
