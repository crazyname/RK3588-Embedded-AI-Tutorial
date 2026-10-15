#!/usr/bin/env python3
"""REAL RKNN-Toolkit2 ONNX converter. Run on supported x86_64 Linux host."""
import argparse
from pathlib import Path

def triples(s):
    v=[float(x) for x in s.split(",")]
    if len(v)!=3:raise argparse.ArgumentTypeError("Use comma-separated 3 values")
    return v

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--onnx",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--mean",type=triples,required=True)
    p.add_argument("--std",type=triples,required=True)
    p.add_argument("--quantize",action="store_true")
    p.add_argument("--dataset",type=Path)
    a=p.parse_args()
    if not a.onnx.is_file():p.error("ONNX file missing")
    if 0 in a.std:p.error("std must be nonzero")
    if a.quantize and (not a.dataset or not a.dataset.is_file()):
        p.error("INT8 needs --dataset (real representative images list)")
    try:
        from rknn.api import RKNN
    except ImportError:
        p.error("RKNN Toolkit2 missing: install matching official host wheel")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    r=RKNN(verbose=True)
    try:
        actions=[
            ("config",lambda:r.config(target_platform="rk3588",
                                      mean_values=[a.mean],std_values=[a.std])),
            ("load_onnx",lambda:r.load_onnx(model=str(a.onnx))),
            ("build",lambda:r.build(do_quantization=a.quantize,
                         **({"dataset":str(a.dataset)} if a.quantize else {}))),
            ("export",lambda:r.export_rknn(str(a.output)))]
        for name,fn in actions:
            print("-->",name,flush=True)
            ret=fn()
            if ret!=0:raise RuntimeError(f"{name} failed, RKNN ret={ret}")
        if not a.output.is_file():raise RuntimeError("No RKNN output generated")
        print("Created",a.output.resolve(),a.output.stat().st_size,"bytes")
    finally:
        r.release()
if __name__=="__main__":
    main()
