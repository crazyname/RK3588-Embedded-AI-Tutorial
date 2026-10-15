#!/usr/bin/env python3
"""第17讲：执行结构化卷积通道剪枝，并同步调整下一层卷积输入通道。"""
import argparse,json
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--weights",type=Path,
        help="NPZ with conv1 shape [out,in,kh,kw] and conv2 [out,in,kh,kw]")
    p.add_argument("--keep-ratio",type=float,default=.75)
    p.add_argument("--output",type=Path,default=Path("build/lesson17/pruned.npz"))
    p.add_argument("--seed",type=int,default=27);a=p.parse_args()
    if not 0<a.keep_ratio<=1:p.error("keep-ratio must be in (0,1]")
    import numpy as np
    if a.weights:
        if not a.weights.is_file():p.error("weights file missing")
        with np.load(a.weights,allow_pickle=False) as z:
            if not {"conv1","conv2"}.issubset(z.files):p.error("NPZ requires conv1 and conv2")
            first=np.asarray(z["conv1"]);second=np.asarray(z["conv2"])
    else:
        rng=np.random.default_rng(a.seed)
        first=rng.normal(size=(16,3,3,3)).astype("float32")
        second=rng.normal(size=(32,16,3,3)).astype("float32")
        print("No --weights: using explicitly synthetic two-layer CNN weights for learning only.")
    if first.ndim!=4 or second.ndim!=4 or second.shape[1]!=first.shape[0]:
        p.error("conv2 must consume the channels produced by conv1")
    n=max(1,round(first.shape[0]*a.keep_ratio))
    scores=np.sum(np.abs(first),axis=(1,2,3))
    keep=np.sort(np.argsort(scores)[-n:])
    pruned1=first[keep,:,:,:];pruned2=second[:,keep,:,:]
    a.output.parent.mkdir(parents=True,exist_ok=True)
    np.savez(a.output,conv1=pruned1,conv2=pruned2,kept_channel_indices=keep)
    print(json.dumps({"original":[list(first.shape),list(second.shape)],
                      "pruned":[list(pruned1.shape),list(pruned2.shape)],
                      "selected_channels":keep.tolist(),"output":str(a.output)},indent=2))
    print("这是实际权重矩阵结构化剪枝，不含训练微调；不代表板端加速或精度回归。")
if __name__=="__main__":main()
