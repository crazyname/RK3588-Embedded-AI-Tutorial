#!/usr/bin/env python3
"""第20讲：真正为多输入 ONNX graph 绑定不同 .npy，并执行 ONNX Runtime。"""
import argparse,json
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--onnx",type=Path,required=True)
    p.add_argument("--inputs",type=Path,required=True,help='JSON object {"input_name":"path.npy",...}')
    p.add_argument("--output",type=Path,default=Path("build/lesson20/outputs.npz"))
    a=p.parse_args()
    if not a.onnx.is_file() or not a.inputs.is_file():p.error("real model and input manifest required")
    import numpy as np
    import onnxruntime as ort
    mapping=json.loads(a.inputs.read_text(encoding="utf8"))
    session=ort.InferenceSession(str(a.onnx),providers=["CPUExecutionProvider"])
    expected={node.name for node in session.get_inputs()}
    if set(mapping)!=expected:p.error(f"expected all input names {expected}; got {set(mapping)}")
    feeds={}
    for spec in session.get_inputs():
        file=Path(mapping[spec.name])
        if not file.is_file():p.error(f"missing array for {spec.name}")
        arr=np.load(file,allow_pickle=False)
        if len(arr.shape)!=len(spec.shape):p.error(f"{spec.name} rank mismatch")
        for need,actual in zip(spec.shape,arr.shape):
            if isinstance(need,int) and need>0 and actual!=need:p.error(f"{spec.name} shape mismatch")
        feeds[spec.name]=arr
    out=session.run(None,feeds)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    np.savez(a.output,**{f"output_{i}":x for i,x in enumerate(out)})
    print(json.dumps({"outputs":[list(o.shape) for o in out],"file":str(a.output)},indent=2))
if __name__=="__main__":main()
