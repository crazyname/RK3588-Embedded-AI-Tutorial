#!/usr/bin/env python3
"""第21讲：对支持动态维度的真实 ONNX 模型执行多个输入形状。"""
import argparse,csv,time
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--onnx",type=Path,required=True);p.add_argument("--inputs",nargs="+",type=Path,required=True)
    p.add_argument("--csv",type=Path,default=Path("build/lesson21/shapes.csv"));a=p.parse_args()
    if not a.onnx.is_file() or any(not x.is_file() for x in a.inputs):p.error("model or one array missing")
    import numpy as np
    import onnxruntime as ort
    session=ort.InferenceSession(str(a.onnx),providers=["CPUExecutionProvider"])
    if len(session.get_inputs())!=1:p.error("Single-input ONNX only")
    name=session.get_inputs()[0].name;record=[]
    for file in a.inputs:
        x=np.load(file,allow_pickle=False)
        start=time.perf_counter();y=session.run(None,{name:x})
        elapsed=(time.perf_counter()-start)*1000
        record.append([str(file),"x".join(map(str,x.shape)),elapsed,";".join(str(o.shape) for o in y)])
    a.csv.parent.mkdir(parents=True,exist_ok=True)
    with a.csv.open("w",newline="",encoding="utf8") as f:
        wr=csv.writer(f);wr.writerow(["file","input_shape","run_ms","output_shapes"]);wr.writerows(record)
    print("Executed ONNX shapes:",record,"report",a.csv)
    print("ONNX dynamic input acceptance does not prove RKNN dynamic shape compatibility.")
if __name__=="__main__":main()
