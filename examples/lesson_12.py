#!/usr/bin/env python3
"""第12讲：用 ONNX protobuf 提取真实图的输入、输出、算子统计与动态 shape。"""
import argparse,collections,json
from pathlib import Path
def shape(value):
    tp=value.type.tensor_type
    return {"name":value.name,"dtype":tp.elem_type,
      "dims":[d.dim_value if d.HasField("dim_value") else d.dim_param or "?" for d in tp.shape.dim]}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--onnx",type=Path,required=True)
    p.add_argument("--output",type=Path,default=Path("build/lesson12/graph.json"))
    a=p.parse_args()
    if not a.onnx.is_file():p.error("ONNX file missing")
    try:import onnx
    except ImportError:p.error("pip install onnx")
    m=onnx.load(str(a.onnx));onnx.checker.check_model(m)
    m=onnx.shape_inference.infer_shapes(m)
    initializer_names={x.name for x in m.graph.initializer}
    info={"model":str(a.onnx),"opsets":[x.version for x in m.opset_import],
      "inputs":[shape(x) for x in m.graph.input if x.name not in initializer_names],
      "outputs":[shape(x) for x in m.graph.output],
      "nodes":len(m.graph.node),"operators":dict(collections.Counter(n.op_type for n in m.graph.node)),
      "layout_sensitive_nodes":[{"name":n.name,"op":n.op_type} for n in m.graph.node if n.op_type in ("Transpose","Reshape","Concat")]}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(info,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(info,ensure_ascii=False,indent=2))
    print("图语法通过 ≠ NPU 算子全支持。可用 Netron 打开相同 ONNX 验证。")
if __name__=="__main__":main()
