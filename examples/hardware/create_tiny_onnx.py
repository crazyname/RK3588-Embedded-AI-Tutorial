#!/usr/bin/env python3
"""Generate a real tiny ONNX Conv/GAP classifier AND deterministic test input.

Host-only model generation needs numpy and onnx. Useful for ONNX Runtime
verification and attempting RKNN conversion without downloading pretrained weights.
NPU SDK compatibility must still be established on the real RK3588 target.
"""
import argparse
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--onnx",type=Path,required=True)
    p.add_argument("--input-npy",type=Path,required=True)
    p.add_argument("--input-raw",type=Path,help="optional raw float32 tensor file")
    args=p.parse_args()
    import numpy as np
    import onnx
    from onnx import helper, TensorProto, numpy_helper

    # NCHW [1,3,4,4]. First output is mean of red channel, second of green.
    w=np.zeros((2,3,1,1),dtype=np.float32)
    w[0,0,0,0]=1.0
    w[1,1,0,0]=1.0
    b=np.zeros((2,),dtype=np.float32)
    nodes=[
        helper.make_node("Conv",["input","conv_weight","conv_bias"],["conv"],name="conv1"),
        helper.make_node("GlobalAveragePool",["conv"],["pooled"],name="gap"),
        helper.make_node("Flatten",["pooled"],["scores"],axis=1,name="flatten")
    ]
    graph=helper.make_graph(
        nodes,"rk3588_tiny_classifier",
        [helper.make_tensor_value_info("input",TensorProto.FLOAT,[1,3,4,4])],
        [helper.make_tensor_value_info("scores",TensorProto.FLOAT,[1,2])],
        initializer=[numpy_helper.from_array(w,name="conv_weight"),
                     numpy_helper.from_array(b,name="conv_bias")])
    model=helper.make_model(graph,opset_imports=[helper.make_opsetid("",13)],
                            producer_name="RK3588-Embedded-AI-Tutorial")
    # Wider ONNX Runtime version compatibility: simple opset-13 graph, IR version 8.
    model.ir_version=8
    onnx.checker.check_model(model)
    args.onnx.parent.mkdir(parents=True,exist_ok=True)
    onnx.save(model,str(args.onnx))

    image=np.zeros((1,3,4,4),dtype=np.float32)
    image[0,0,:,:]=np.linspace(0,1,16,dtype=np.float32).reshape(4,4)
    image[0,1,:,:]=0.25
    image[0,2,:,:]=0.80
    args.input_npy.parent.mkdir(parents=True,exist_ok=True)
    np.save(args.input_npy,image)
    if args.input_raw:
        args.input_raw.parent.mkdir(parents=True,exist_ok=True)
        args.input_raw.write_bytes(image.tobytes(order="C"))
    print("ONNX:",args.onnx)
    print("input:",args.input_npy,"shape:",image.shape,"dtype:",image.dtype)
    print("Expected ONNX Runtime output [red mean, green mean] = [0.5, 0.25]")
    print("NOTE: This toy model is not a real image recognizer; it tests the inference toolchain.")
if __name__=="__main__":
    main()
