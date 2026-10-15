"""Offline/CI tests. Mocked SDK behavior here is NOT a real NPU test."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest

ROOT=Path(__file__).resolve().parents[1]
def load_file(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

probe=load_file("rock5b_probe",ROOT/"tools"/"board_probe.py")
camera=load_file("rock5b_camera",ROOT/"tools"/"usb_camera_check.py")
official=load_file("rock5b_official",ROOT/"tools"/"run_official_yolov8.py")
mobilenet=load_file("rock5b_mobile",ROOT/"apps"/"mobilenet_image_lite.py")

class BoardProfileTests(unittest.TestCase):
    def test_original_board_detection(self):
        self.assertTrue(probe.is_rock5b("Radxa ROCK 5B"))
        self.assertTrue(probe.is_rock5b("Radxa ROCK 5 Model B"))
        self.assertTrue(probe.is_rock5b(None,["radxa,rock-5b","rockchip,rk3588"]))
        for model in ("Radxa ROCK 5B+", "Radxa ROCK 5B Plus",
                      "Orange Pi 5 Plus","Radxa ROCK 5A"):
            with self.subTest(model=model):
                self.assertFalse(probe.is_rock5b(model))
        self.assertFalse(probe.is_rock5b(None,["radxa,rock-5b-plus"]))
    def test_probe_read_only_output(self):
        result=probe.build_report()
        self.assertIn("matches_rock5b",result)
        self.assertIn("npu_evidence",result)
        for forbidden in ("mac_address","serial_number","wifi_password"):
            self.assertNotIn(forbidden,result)
    def test_camera_source_normalization(self):
        self.assertEqual(camera.source_value("0"),0)
        self.assertEqual(camera.source_value("/dev/video2"),"/dev/video2")
    def test_official_command_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with self.assertRaises(FileNotFoundError):
                official.command_for(root,"python3",None,False)
            (root/"python").mkdir()
            (root/"model").mkdir()
            (root/"python"/"yolov8.py").write_text("# fake script\n")
            (root/"model"/"yolov8.rknn").write_bytes(b"fake model")
            cmd,cwd=official.command_for(root,"python3",None,True)
            self.assertEqual(cmd[0],"python3")
            self.assertEqual(cmd[-1],"--img_save")
            self.assertEqual(cwd,root/"python")

class ImageClassificationTests(unittest.TestCase):
    def test_pillow_preprocessing(self):
        import numpy as np
        from PIL import Image
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/"sample.png"
            Image.new("RGB",(6,6),(255,0,17)).save(source)
            x=mobilenet.make_input(source,(4,4),"stretch")
            self.assertEqual(x.shape,(4,4,3))
            self.assertEqual(x.dtype,np.uint8)
            self.assertTrue((x[0,0]==[255,0,17]).all())
    def test_topk_from_real_numpy(self):
        import numpy as np
        values=np.array([[.3,.9,.1,.6]],dtype=np.float32)
        top,count=mobilenet.topk_scores(values,2)
        self.assertEqual(count,4)
        self.assertEqual([x[0] for x in top],[1,3])
    def test_runtime_control_flow_mock(self):
        import numpy as np
        events=[]
        class Fake:
            def load_rknn(self,filename):
                events.append("load")
                return 0
            def init_runtime(self):
                events.append("init")
                return 0
            def inference(self,inputs):
                events.append("infer")
                return [np.array([[.25,.75]],dtype=np.float32)]
            def release(self):
                events.append("release")
        package=types.ModuleType("rknnlite")
        api=types.ModuleType("rknnlite.api")
        api.RKNNLite=Fake
        old_pkg=sys.modules.get("rknnlite")
        old_api=sys.modules.get("rknnlite.api")
        try:
            sys.modules["rknnlite"]=package
            sys.modules["rknnlite.api"]=api
            out,ms=mobilenet.run(Path("/tmp/test.rknn"),
                                 np.zeros((2,2,3),dtype=np.uint8),runs=2,warmup=1)
            self.assertEqual(out.shape,(1,2))
            self.assertEqual(len(ms),2)
            self.assertEqual(events,["load","init","infer","infer","infer","release"])
        finally:
            if old_pkg is None:sys.modules.pop("rknnlite",None)
            else:sys.modules["rknnlite"]=old_pkg
            if old_api is None:sys.modules.pop("rknnlite.api",None)
            else:sys.modules["rknnlite.api"]=old_api

if __name__=="__main__":
    unittest.main()
