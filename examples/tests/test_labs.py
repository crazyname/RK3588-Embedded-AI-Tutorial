import unittest
from pathlib import Path
import tempfile
from examples.labs import quantize, iou, nms, letterbox_transform, from_letterbox, check_yolo_labels, percentiles, exec_lesson
from types import SimpleNamespace

class LessonTests(unittest.TestCase):
    def test_quant(self):
        self.assertEqual(quantize(.26,.1)['int8'],3)
        self.assertAlmostEqual(quantize(.26,.1)['dequantized'],.3)
    def test_iou_and_nms(self):
        self.assertEqual(iou([0,0,10,10],[0,0,10,10]),1.)
        self.assertEqual(len(nms([{'box':[0,0,10,10],'score':.9,'class_id':0},{'box':[0,0,10,10],'score':.5,'class_id':0}])),1)
    def test_letterbox_inverse(self):
        t=letterbox_transform(1280,720)
        self.assertAlmostEqual(t['pad_y'],140)
        self.assertEqual(from_letterbox([100,190,200,290],t,1280,720),[200,100,400,300])
    def test_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'test.txt'
            p.write_text('0 0.5 0.5 0.4 0.2\n',encoding='utf8')
            self.assertTrue(check_yolo_labels(Path(tmp))['passed'])
            p.write_text('0 1.0 1.0 0.5 0.4\n',encoding='utf8')
            self.assertFalse(check_yolo_labels(Path(tmp))['passed'])
    def test_statistics(self):
        self.assertEqual(percentiles([2,4,6,8])['p50'],5)
    def test_portable_all(self):
        dependent={9,11,12,16,18}
        for n in range(35):
            if n in dependent: continue
            with self.subTest(lesson=n):
                result=exec_lesson(n,SimpleNamespace(input=None,output=None))
                self.assertIsNotNone(result)

if __name__=='__main__':
    unittest.main()
