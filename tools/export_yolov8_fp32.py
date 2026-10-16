#!/usr/bin/env python3
"""Export actual RKNNLite output_0..output_N FP32 NCHW tensors for C++ YOLOv8 replay.

The input NPZ may come from a real board or a PC fixture. This tool does not
infer provenance, execute RKNN, or invent missing model outputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda:src.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def export(npz_path,output_dir,grids=(80,40,20)):
    if len(grids)!=3 or not all(g>0 for g in grids) or not(grids[0]>grids[1]>grids[2]):
        raise ValueError("Three strictly descending positive head grids are required")
    output_dir.mkdir(parents=True,exist_ok=True)
    records=[]
    with np.load(npz_path,allow_pickle=False) as contents:
        indices=sorted(int(k[7:]) for k in contents.files if
                       k.startswith("output_") and k[7:].isdigit())
        if indices not in (list(range(6)),list(range(9))):
            raise ValueError("Expected exactly output_0..output_5 or output_0..output_8")
        if len(contents.files)!=len(indices):
            raise ValueError("Unexpected tensors in NPZ")
        per_head=len(indices)//3
        for n in indices:
            name=f"output_{n}"
            data=contents[name]
            grid=grids[n//per_head]
            channels=(64 if n%per_head==0 else (80 if n%per_head==1 else 1))
            expected=(1,channels,grid,grid)
            if data.shape!=expected or data.dtype!=np.float32:
                raise ValueError(f"{name}: expected {expected} float32 NCHW, got {data.shape} {data.dtype}")
            if not np.isfinite(data).all():
                raise ValueError(f"{name} includes NaN or Infinity")
            # ensure C-contiguous NCHW payload, no array strides or endian ambiguity
            raw=np.ascontiguousarray(data.astype("<f4",copy=False))
            target=output_dir/f"out_{n}.f32"
            target.write_bytes(raw.tobytes(order="C"))
            records.append({"name":name,"shape":list(expected),"dtype":"little-endian float32",
                            "file":target.name,"sha256":sha256(target)})
    report={"source_npz":str(npz_path),"source_sha256":sha256(npz_path),
            "output_tensors":len(records),"grids":list(grids),
            "files":records,
            "note":"Exact file export only. Provenance as real NPU outputs must be independently established via board logs."}
    (output_dir/"manifest.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--npz",type=Path,required=True)
    p.add_argument("--out-dir",type=Path,required=True)
    p.add_argument("--grids",nargs=3,type=int,default=(80,40,20),
                   metavar=("GRID0","GRID1","GRID2"))
    a=p.parse_args()
    try:
        result=export(a.npz,a.out_dir,a.grids)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError,KeyError) as exc:
        print("ERROR:",exc)
        return 1

if __name__=="__main__":
    raise SystemExit(main())
