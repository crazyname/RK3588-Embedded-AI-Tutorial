"""Tests for the real, standalone Lesson 27 MobileNet pipeline."""
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from PIL import Image
from examples import lesson_27 as m

class Lesson27Tests(unittest.TestCase):
    def test_preprocessing_onnx(self):
        with tempfile.TemporaryDirectory() as temp:
            pic = Path(temp)/"red.png"
            Image.new("RGB",(4,4),(255,0,0)).save(pic)
            t = m.prepare_image(pic,4,4,"squash","RGB","auto","auto","onnx")
            self.assertEqual(t.shape,(1,3,4,4))
            self.assertEqual(t.dtype,np.float32)
            self.assertAlmostEqual(float(t[0,0,0,0]),(1-0.485)/0.229,places=5)
    def test_preprocessing_rknn(self):
        with tempfile.TemporaryDirectory() as temp:
            pic=Path(temp)/"red.png"
            Image.new("RGB",(4,4),(255,0,0)).save(pic)
            t=m.prepare_image(pic,4,4,"squash","BGR","auto","auto","rknn")
            self.assertEqual(t.shape,(1,4,4,3))
            self.assertEqual(t.dtype,np.uint8)
            self.assertEqual(list(t[0,0,0]),[0,0,255])
    def test_probabilities(self):
        logits = m.probabilities(np.asarray([[0.,2.]]))
        self.assertEqual(logits.shape,(2,))
        self.assertGreater(float(logits[1]),float(logits[0]))
        with self.assertRaises(ValueError):
            m.probabilities(np.asarray([1.,2.]),"probabilities")
    def test_labels_count(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"labels.txt"
            path.write_text("background\nbell\ncat\n")
            self.assertEqual(m.read_labels(path,2,1),["bell","cat"])
            with self.assertRaises(ValueError):
                m.read_labels(path,2,0)
    def test_no_stub(self):
        source = Path(m.__file__).read_text()
        self.assertNotIn("from labs import main",source)
        self.assertIn("InferenceSession",source)
        self.assertIn("RKNNLite",source)

if __name__=="__main__":
    unittest.main()
