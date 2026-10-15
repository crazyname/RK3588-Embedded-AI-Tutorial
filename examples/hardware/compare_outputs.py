#!/usr/bin/env python3
"""Compare actual ONNX Runtime and RKNN output .npz files numerically."""
import argparse
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--reference",type=Path,required=True)
    ap.add_argument("--candidate",type=Path,required=True)
    ap.add_argument("--atol",type=float,default=1e-3)
    ap.add_argument("--rtol",type=float,default=1e-2)
    a=ap.parse_args()
    if not a.reference.is_file() or not a.candidate.is_file():
        ap.error("missing NPZ file")
    import numpy as np
    with np.load(a.reference,allow_pickle=False) as ref,np.load(a.candidate,allow_pickle=False) as cand:
        if set(ref.files)!=set(cand.files):
            raise ValueError(f"Different tensor names: {ref.files} != {cand.files}")
        failed=False
        for name in sorted(ref.files):
            x=np.asarray(ref[name])
            y=np.asarray(cand[name])
            if x.shape!=y.shape:
                print(name,"shape mismatch:",x.shape,y.shape)
                failed=True
                continue
            delta=np.abs(x.astype(np.float64)-y.astype(np.float64))
            ok=np.allclose(x,y,atol=a.atol,rtol=a.rtol,equal_nan=False)
            print(name,"shape=",x.shape,"max_abs=",float(np.max(delta)),
                  "mean_abs=",float(np.mean(delta)),"allclose=",ok)
            failed=failed or not ok
    if failed:raise SystemExit(1)
if __name__=="__main__":
    main()
