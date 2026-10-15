#!/usr/bin/env python3
"""第24讲：真正通过 RKNN-Toolkit-Lite2 加载多输出模型并写入 NPZ 与 JSON。"""
import argparse,json,statistics,time
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--rknn",type=Path,required=True)
    p.add_argument("--input-npy",type=Path,required=True);p.add_argument("--output",type=Path,default=Path("build/lesson24/output.npz"))
    p.add_argument("--warmup",type=int,default=5);p.add_argument("--runs",type=int,default=20)
    a=p.parse_args()
    if not a.rknn.is_file() or not a.input_npy.is_file():p.error("model/input missing")
    if a.warmup<0 or a.runs<1:p.error("warmup>=0 runs>=1 required")
    import numpy as np
    try:from rknnlite.api import RKNNLite
    except ImportError:p.error("RKNNLite unavailable; use matching RK3588 board SDK")
    x=np.load(a.input_npy,allow_pickle=False);r=RKNNLite()
    try:
        status=r.load_rknn(str(a.rknn))
        if status:raise RuntimeError(f"load_rknn status={status}")
        status=r.init_runtime()
        if status:raise RuntimeError(f"init_runtime status={status}")
        def infer():
            out=r.inference(inputs=[x])
            if not out:raise RuntimeError("RKNNLite inference failed")
            return out
        for _ in range(a.warmup):infer()
        timings=[]
        for _ in range(a.runs):
            t0=time.perf_counter();out=infer()
            timings.append((time.perf_counter()-t0)*1000)
        a.output.parent.mkdir(parents=True,exist_ok=True)
        np.savez(a.output,**{f"output_{i}":np.asarray(v) for i,v in enumerate(out)})
        report={"input_shape":list(x.shape),"output_shapes":[list(np.shape(v)) for v in out],
                "mean_call_ms":statistics.mean(timings),"runs":a.runs}
        a.output.with_suffix(".json").write_text(json.dumps(report,indent=2)+"\n")
        print(json.dumps(report,indent=2))
    finally:r.release()
if __name__=="__main__":main()
