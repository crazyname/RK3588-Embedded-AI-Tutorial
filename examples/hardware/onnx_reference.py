#!/usr/bin/env python3
"""Execute actual ONNX Runtime with a .npy input; saves raw tensor outputs."""
import argparse
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--onnx",type=Path,required=True)
    ap.add_argument("--input-npy",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    if not a.onnx.is_file() or not a.input_npy.is_file():
        ap.error("ONNX or numpy input file missing")
    import numpy as np
    import onnxruntime as ort
    session=ort.InferenceSession(str(a.onnx),providers=["CPUExecutionProvider"])
    inputs=session.get_inputs()
    if len(inputs)!=1:ap.error("This example accepts single-input models only")
    x=np.load(a.input_npy,allow_pickle=False)
    print("Input",inputs[0].name,x.shape,x.dtype)
    out=session.run(None,{inputs[0].name:x})
    a.output.parent.mkdir(parents=True,exist_ok=True)
    np.savez(a.output,**{"output_"+str(i):y for i,y in enumerate(out)})
    for i,y in enumerate(out):print("Output",i,y.shape,y.dtype)
    print("Saved",a.output)
if __name__=="__main__":
    main()
