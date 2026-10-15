#!/usr/bin/env python3
"""第14讲：比较真实浮点和量化推理 NPZ 张量，计算误差与类别一致性。"""
import argparse,json
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--float",dest="fp",type=Path,required=True)
    p.add_argument("--quantized",type=Path,required=True)
    p.add_argument("--max-mae",type=float,help="设置后严格判断 MAE 阈值")
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    if not a.fp.is_file() or not a.quantized.is_file():p.error("Both real NPZ files required")
    import numpy as np
    report=[];failed=False
    with np.load(a.fp,allow_pickle=False) as src,np.load(a.quantized,allow_pickle=False) as dst:
        if set(src.files)!=set(dst.files):p.error("Tensor names differ")
        for name in src.files:
            x=np.asarray(src[name],dtype=np.float64);y=np.asarray(dst[name],dtype=np.float64)
            if x.shape!=y.shape:p.error(f"Shape mismatch for {name}: {x.shape} vs {y.shape}")
            d=x-y;mae=float(np.mean(np.abs(d)));rmse=float(np.sqrt(np.mean(d*d)))
            cos=float(np.dot(x.ravel(),y.ravel())/(np.linalg.norm(x)*np.linalg.norm(y))) if np.linalg.norm(x)*np.linalg.norm(y)>0 else None
            report.append({"name":name,"shape":list(x.shape),"mae":mae,"rmse":rmse,
                           "max_abs":float(np.max(np.abs(d))),"cosine":cos,
                           "top1_equal":bool(np.argmax(x)==np.argmax(y))})
            failed|=a.max_mae is not None and mae>a.max_mae
    s=json.dumps(report,indent=2,ensure_ascii=False)
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(s+"\n")
    print(s)
    print("注意：张量误差不能替代分类准确率或目标检测 mAP。")
    if failed:raise SystemExit(1)
if __name__=="__main__":main()
