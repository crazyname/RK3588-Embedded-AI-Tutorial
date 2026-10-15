#!/usr/bin/env python3
"""Actual RK3588 RKNNLite inference, requires prepared tensor .npy and target board."""
import argparse
from pathlib import Path
import time

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--rknn",type=Path,required=True)
    ap.add_argument("--input-npy",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--warmup",type=int,default=5)
    ap.add_argument("--runs",type=int,default=20)
    a=ap.parse_args()
    if a.warmup<0 or a.runs<1:ap.error("warmup>=0 and runs>=1")
    if not a.rknn.is_file() or not a.input_npy.is_file():ap.error("Missing input file")
    import numpy as np
    from rknnlite.api import RKNNLite
    x=np.load(a.input_npy,allow_pickle=False)
    print("Prepared input:",x.shape,x.dtype)
    r=RKNNLite()
    try:
        ret=r.load_rknn(str(a.rknn))
        if ret!=0:raise RuntimeError(f"load_rknn failed: {ret}")
        ret=r.init_runtime()
        if ret!=0:raise RuntimeError(f"init_runtime failed: {ret}")
        for _ in range(a.warmup):
            if r.inference(inputs=[x]) is None:raise RuntimeError("warmup failed")
        samples=[]
        for _ in range(a.runs):
            start=time.perf_counter_ns()
            output=r.inference(inputs=[x])
            samples.append((time.perf_counter_ns()-start)/1e6)
            if output is None:raise RuntimeError("inference returned None")
        a.output.parent.mkdir(parents=True,exist_ok=True)
        np.savez(a.output,**{f"output_{i}":np.asarray(y) for i,y in enumerate(output)})
        for i,y in enumerate(output):print(i,np.asarray(y).shape,np.asarray(y).dtype)
        print("RKNNLite inference call mean ms:",sum(samples)/len(samples))
        print("NOT end-to-end camera/display FPS")
    finally:
        r.release()
if __name__=="__main__":
    main()
