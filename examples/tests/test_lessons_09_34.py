"""Functional regression tests for independent lessons 09–34.

These execute *real* ONNX models, NumPy arrays, images, and filesystem operations.
They do not claim that RK3588 NPU / RKLLM has been tested on GitHub's x86 runner.
"""
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import onnx
from onnx import TensorProto, helper
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
PY=sys.executable

def execute(n,*args,success=True):
    cmd=[PY,str(ROOT/"examples"/f"lesson_{n:02d}.py"),*map(str,args)]
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=40)
    if success and p.returncode:
        raise AssertionError(f"lesson {n} exit {p.returncode}\n{p.stdout}\n{p.stderr}")
    if not success and not p.returncode:
        raise AssertionError(f"lesson {n} unexpectedly succeeded")
    return p

def write_graph(path,nodes,inputs,outputs,initializers=()):
    g=helper.make_graph(nodes,"ci_fixture",inputs,outputs,initializer=list(initializers))
    m=helper.make_model(g,opset_imports=[helper.make_opsetid("",13)])
    m.ir_version=8
    onnx.checker.check_model(m)
    onnx.save(m,str(path))

class RealArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.dir=Path(cls.temp.name)
        cls.tiny=cls.dir/"tiny.onnx"
        cls.tensor=cls.dir/"input.npy"
        cls.raw=cls.dir/"input.raw"
        p=subprocess.run([PY,str(ROOT/"examples/hardware/create_tiny_onnx.py"),
            "--onnx",str(cls.tiny),"--input-npy",str(cls.tensor),
            "--input-raw",str(cls.raw)],capture_output=True,text=True,timeout=25)
        if p.returncode:raise RuntimeError(p.stderr)
        cls.image=cls.dir/"sample.png"
        Image.new("RGB",(4,4),(128,64,0)).save(cls.image)
        cls.labels=cls.dir/"labels.txt"
        cls.labels.write_text("red\ngreen\n",encoding="utf8")
    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_09_invalid_onnx_fails_before_sdk(self):
        invalid=self.dir/"invalid.onnx"
        invalid.write_bytes(b"this is not an ONNX model")
        p=execute(9,"--onnx",invalid,"--output",self.dir/"invalid.rknn",success=False)
        self.assertTrue(p.stderr or p.stdout)
        self.assertFalse((self.dir/"invalid.rknn").exists())

    def test_10_image_numeric_preprocessing(self):
        out=self.dir/"lesson10.npy"
        execute(10,"--image",self.image,"--height",4,"--width",4,
                "--mean","0,0,0","--std","1,1,1","--output",out)
        arr=np.load(out)
        self.assertEqual(arr.shape,(1,3,4,4))
        self.assertAlmostEqual(float(arr[0,0,0,0]),128/255,places=6)
        self.assertAlmostEqual(float(arr[0,1,0,0]),64/255,places=6)

    def test_12_onnx_operator_summary(self):
        out=self.dir/"summary.json"
        execute(12,"--onnx",self.tiny,"--output",out)
        info=json.loads(out.read_text(encoding="utf8"))
        self.assertEqual(info["operators"]["Conv"],1)
        self.assertEqual(info["operators"]["GlobalAveragePool"],1)
        self.assertEqual(info["inputs"][0]["dims"],[1,3,4,4])

    def test_14_quantization_comparison_and_failure_threshold(self):
        source=self.dir/"reference.npz"
        candidate=self.dir/"quantized.npz"
        np.savez(source,output_0=np.array([[0.,1.,2.]],dtype=np.float32))
        np.savez(candidate,output_0=np.array([[0.,1.,2.3]],dtype=np.float32))
        report=self.dir/"comparison.json"
        execute(14,"--float",source,"--quantized",candidate,
                "--max-mae",.2,"--output",report)
        rows=json.loads(report.read_text(encoding="utf8"))
        self.assertEqual(len(rows),1)
        self.assertAlmostEqual(rows[0]["mae"],.1,places=5)
        self.assertTrue(rows[0]["top1_equal"])
        execute(14,"--float",source,"--quantized",candidate,
                "--max-mae",.01,success=False)

    def test_17_actual_structured_pruning_dimensions(self):
        output=self.dir/"pruned.npz"
        execute(17,"--keep-ratio",".5","--output",output)
        with np.load(output) as z:
            self.assertEqual(z["conv1"].shape,(8,3,3,3))
            self.assertEqual(z["conv2"].shape,(32,8,3,3))
            self.assertEqual(len(z["kept_channel_indices"]),8)
        execute(17,"--keep-ratio","-1",success=False)

    def test_19_batch_real_images(self):
        path=self.dir/"batch.npy"
        execute(19,"--images",self.image,self.image,"--batch",2,
                "--width",4,"--height",4,"--output",path)
        arr=np.load(path)
        self.assertEqual(arr.shape,(2,4,4,3))
        self.assertEqual(arr.dtype,np.uint8)
        self.assertTrue(np.all(arr[0]==arr[1]))
        execute(19,"--images",self.image,"--batch",2,success=False)

    def test_20_onnx_runtime_genuine_multi_input(self):
        model=self.dir/"add_inputs.onnx"
        inp=[helper.make_tensor_value_info(n,TensorProto.FLOAT,[1,2]) for n in ("x","y")]
        out=[helper.make_tensor_value_info("sum",TensorProto.FLOAT,[1,2])]
        write_graph(model,[helper.make_node("Add",["x","y"],["sum"])],inp,out)
        x=self.dir/"x.npy";y=self.dir/"y.npy"
        np.save(x,np.array([[1.,2.]],dtype=np.float32))
        np.save(y,np.array([[3.,5.]],dtype=np.float32))
        mapping=self.dir/"inputs.json"
        mapping.write_text(json.dumps({"x":str(x),"y":str(y)}),encoding="utf8")
        output=self.dir/"multi.npz"
        execute(20,"--onnx",model,"--inputs",mapping,"--output",output)
        with np.load(output) as npz:
            np.testing.assert_array_equal(npz["output_0"],[[4.,7.]])
        mapping.write_text(json.dumps({"x":str(x)}),encoding="utf8")
        execute(20,"--onnx",model,"--inputs",mapping,success=False)

    def test_21_real_dynamic_dimension_inference(self):
        model=self.dir/"dynamic.onnx"
        inp=[helper.make_tensor_value_info("input",TensorProto.FLOAT,["batch",2])]
        out=[helper.make_tensor_value_info("output",TensorProto.FLOAT,["batch",2])]
        write_graph(model,[helper.make_node("Identity",["input"],["output"])],inp,out)
        paths=[]
        for i in (1,3):
            p=self.dir/f"shape_{i}.npy"
            np.save(p,np.ones((i,2),dtype=np.float32))
            paths.append(p)
        output=self.dir/"shapes.csv"
        execute(21,"--onnx",model,"--inputs",*paths,"--csv",output)
        with output.open(newline="",encoding="utf8") as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),2)
        self.assertEqual([x["input_shape"] for x in rows],["1x2","3x2"])

    def test_22_onnx_identity_removal_preserves_outputs(self):
        model=self.dir/"with_identity.onnx"
        inp=[helper.make_tensor_value_info("a",TensorProto.FLOAT,[1,2])]
        out=[helper.make_tensor_value_info("result",TensorProto.FLOAT,[1,2])]
        bias=onnx.numpy_helper.from_array(np.array([[1.,2.]],dtype=np.float32),name="b")
        nodes=[helper.make_node("Add",["a","b"],["intermediate"]),
               helper.make_node("Identity",["intermediate"],["result"])]
        write_graph(model,nodes,inp,out,[bias])
        array=self.dir/"identity_input.npy"
        np.save(array,np.array([[3.,4.]],dtype=np.float32))
        target=self.dir/"rewritten.onnx"
        execute(22,"--onnx",model,"--output",target,"--input-npy",array)
        verified=onnx.load(str(target))
        onnx.checker.check_model(verified)
        self.assertEqual([n.op_type for n in verified.graph.node],["Add"])

    def test_23_real_onnx_generates_cpp_interface(self):
        output=self.dir/"tensors.hpp"
        execute(23,"--onnx",self.tiny,"--output",output,"--compile")
        text=output.read_text(encoding="utf8")
        self.assertIn("TensorDescription",text)
        self.assertIn("input_count=1",text)
        self.assertIn("output_count=1",text)

    def test_26_buffer_preflight_not_claimed_as_zero_copy(self):
        raw_size=self.raw.stat().st_size
        report=self.dir/"zero_copy_manifest.json"
        execute(26,"--model",self.tiny,"--input-raw",self.raw,
                "--native-input-bytes",raw_size,"--output",report)
        manifest=json.loads(report.read_text())
        self.assertTrue(manifest["preflight_ok"])
        self.assertFalse(manifest["zero_copy_executed"])
        execute(26,"--model",self.tiny,"--input-raw",self.raw,
                "--native-input-bytes",raw_size+1,success=False)

    def test_28_onnx_classifier_real_image(self):
        output=self.dir/"classification.json"
        execute(28,"--onnx",self.tiny,"--images",self.image,"--labels",self.labels,
                "--width",4,"--height",4,"--topk",2,"--output",output)
        prediction=json.loads(output.read_text(encoding="utf8"))
        self.assertEqual(len(prediction),1)
        self.assertEqual(prediction[0]["topk"][0]["index"],0)
        self.assertEqual(prediction[0]["topk"][0]["label"],"red")
        bad=self.dir/"bad_labels.txt"
        bad.write_text("only one\n",encoding="utf8")
        execute(28,"--onnx",self.tiny,"--images",self.image,"--labels",bad,
                "--width",4,"--height",4,success=False)

    def test_31_yolo_label_validations(self):
        folder=self.dir/"yolo_labels"
        folder.mkdir(exist_ok=True)
        file=folder/"one.txt"
        file.write_text("0 0.5 0.5 0.4 0.3\n",encoding="utf8")
        out=self.dir/"labels_report.json"
        execute(31,"--labels",folder,"--report",out)
        report=json.loads(out.read_text(encoding="utf8"))
        self.assertEqual(report["valid_boxes"],1)
        self.assertEqual(report["errors"],[])
        file.write_text("0 0.99 0.99 0.4 0.3\n",encoding="utf8")
        execute(31,"--labels",folder,"--report",out,success=False)

    def test_34_no_claim_without_actual_rkllm_binary(self):
        model=self.dir/"dummy_model.rkllm"
        model.write_bytes(b"not a real RKLLM model - negative case only")
        missing=self.dir/"missing_rkllm_executable"
        execute(34,"--program",missing,"--model",model,
                "--prompt","test",success=False)

if __name__=="__main__":
    unittest.main()
