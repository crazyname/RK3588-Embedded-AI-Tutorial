"""CPU fixture tests for letterbox reference comparison, NOT physical RGA validation."""
import unittest
import numpy as np
from tools.compare_rga_letterbox import assess,reference

class RgaImageComparisonTests(unittest.TestCase):
    def test_perfect_software_reference(self):
        img=np.zeros((4,8,3),dtype=np.uint8)
        img[:,:,0]=120
        img[:,:,1]=60
        img[:,:,2]=5
        ref,meta=reference(img.ravel(),8,4,size=16)
        self.assertEqual((meta["left"],meta["top"]), (0,4))
        result=assess(img.tobytes(),ref.tobytes(),8,4,max_mean_error=0,size=16)
        self.assertTrue(result["passed"])
        self.assertEqual(result["mean_abs_error_rgb"],0)
    def test_changed_pixels_detected(self):
        img=np.full((4,4,3),100,dtype=np.uint8)
        ref,_=reference(img.ravel(),4,4,size=8)
        modified=ref.copy()
        modified[:]=50
        result=assess(img.tobytes(),modified.tobytes(),4,4,
                      max_mean_error=1,size=8)
        self.assertFalse(result["passed"])
    def test_nonblack_padding_rejected(self):
        source=np.full((2,4,3),50,dtype=np.uint8)
        ref,_=reference(source.ravel(),4,2,size=8)
        ref[0,0,0]=1
        with self.assertRaisesRegex(ValueError,"padding"):
            assess(source.tobytes(),ref.tobytes(),4,2,size=8)
    def test_bad_input_output_and_threshold(self):
        with self.assertRaises(ValueError):
            assess(b"few",bytes(8*8*3),4,4,size=8)
        with self.assertRaises(ValueError):
            assess(bytes(4*4*3),b"bad",4,4,size=8)
        with self.assertRaises(ValueError):
            assess(bytes(4*4*3),bytes(8*8*3),4,4,max_mean_error=-1,size=8)

if __name__=="__main__":
    unittest.main()
