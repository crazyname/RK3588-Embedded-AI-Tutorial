#!/usr/bin/env python3
"""第22讲：保语义地删除真实 ONNX 中的 Identity 节点并校验。"""
import argparse
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--onnx",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--input-npy",type=Path,help="Optional numerical regression using ONNX Runtime")
    a=p.parse_args()
    if not a.onnx.is_file():p.error("ONNX file missing")
    if a.onnx.resolve()==a.output.resolve():p.error("Output must differ from source")
    import onnx
    model=onnx.load(str(a.onnx));onnx.checker.check_model(model)
    # For safety handle only plain single-input/single-output Identity nodes,
    # and rewire all consumers including graph outputs. Never edit subgraphs.
    removed=0
    for node in list(model.graph.node):
        if node.op_type!="Identity" or len(node.input)!=1 or len(node.output)!=1:continue
        src,dst=node.input[0],node.output[0]
        if src==dst:continue
        for candidate in model.graph.node:
            if candidate is node:continue
            for j,key in enumerate(candidate.input):
                if key==dst:candidate.input[j]=src
        for output in model.graph.output:
            if output.name==dst:output.name=src
        model.graph.node.remove(node);removed+=1
    onnx.checker.check_model(model)
    if a.input_npy:
        if not a.input_npy.is_file():p.error("Regression input missing")
        import numpy as np
        import onnxruntime as ort
        before=ort.InferenceSession(str(a.onnx),providers=["CPUExecutionProvider"])
        after=ort.InferenceSession(model.SerializeToString(),providers=["CPUExecutionProvider"])
        if len(before.get_inputs())!=1 or len(after.get_inputs())!=1:p.error("Single-input only for regression")
        x=np.load(a.input_npy,allow_pickle=False)
        lhs=before.run(None,{before.get_inputs()[0].name:x})
        rhs=after.run(None,{after.get_inputs()[0].name:x})
        if len(lhs)!=len(rhs) or any(not np.allclose(u,v,rtol=1e-5,atol=1e-6) for u,v in zip(lhs,rhs)):
            raise SystemExit("Numerical regression failed: not exporting rewritten model")
    a.output.parent.mkdir(parents=True,exist_ok=True);onnx.save(model,str(a.output))
    print("Removed Identity nodes:",removed,"saved",a.output)
    print("Generic graph edits require stronger regression than ONNX checker alone.")
if __name__=="__main__":main()
