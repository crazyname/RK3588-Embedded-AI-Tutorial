#!/usr/bin/env python3
"""第13讲：在官方 Toolkit2 上真正调用 RKNN 推理并存储原始输出张量。"""
import argparse,json,statistics,time
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rknn",type=Path,required=True);p.add_argument("--input-npy",type=Path,required=True)
    p.add_argument("--output",type=Path,default=Path("build/lesson13/rknn.npz"))
    p.add_argument("--target",choices=("simulator","rk3588"),default="simulator")
    p.add_argument("--runs",type=int,default=5)
    a=p.parse_args()
    if not a.rknn.is_file() or not a.input_npy.is_file():p.error("real model and numpy input required")
    if a.runs<1:p.error("runs must be positive")
    import numpy as np
    try:from rknn.api import RKNN
    except ImportError:p.error("RKNN-Toolkit2 required on supported x86_64 host")
    tensor=np.load(a.input_npy,allow_pickle=False);r=RKNN()
    try:
        rc=r.load_rknn(str(a.rknn))
        if rc!=0:raise RuntimeError(f"load_rknn={rc}")
        rc=r.init_runtime() if a.target=="simulator" else r.init_runtime(target="rk3588")
        if rc!=0:raise RuntimeError(f"init_runtime={rc}")
        durations=[]
        for _ in range(a.runs):
            t0=time.perf_counter();out=r.inference(inputs=[tensor])
            durations.append((time.perf_counter()-t0)*1000)
            if out is None:raise RuntimeError("inference returned None")
        a.output.parent.mkdir(parents=True,exist_ok=True)
        np.savez(a.output,**{f"output_{i}":v for i,v in enumerate(out)})
        print(json.dumps({"target":a.target,"shapes":[list(np.shape(x)) for x in out],
            "mean_call_ms":statistics.mean(durations),"output":str(a.output)},indent=2))
        print("Simulator duration is not RK3588 hardware performance.")
    finally:r.release()
if __name__=="__main__":main()
