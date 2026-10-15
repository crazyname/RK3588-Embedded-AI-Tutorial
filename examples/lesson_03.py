#!/usr/bin/env python3
"""第03讲：根据状态清单生成模型部署有向依赖图和缺失步骤。"""
import argparse,json
from pathlib import Path
STAGES=[("onnx","ONNX 模型校验"),("convert","Toolkit2 转换"),("runtime","Runtime/Driver"),("input","输入预处理"),("inference","真实推理"),("accuracy","精度验收")]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--status",type=Path,help='JSON 如 {"onnx":true,"convert":true}')
    p.add_argument("--dot",type=Path,default=Path("build/lesson03/pipeline.dot"));a=p.parse_args()
    data=json.loads(a.status.read_text(encoding="utf8")) if a.status else {}
    if not isinstance(data,dict):p.error("status must be a JSON object")
    keys={x for x,_ in STAGES}
    if set(data)-keys:p.error("unknown steps: "+",".join(sorted(set(data)-keys)))
    if any(type(v) is not bool for v in data.values()):p.error("step state must be boolean")
    lines=["digraph RKNN {","  rankdir=LR;"]
    for name,label in STAGES:
        color="palegreen" if data.get(name) is True else "lightgray"
        lines.append(f'  {name} [label="{label}",style=filled,fillcolor="{color}"];')
    lines += [f"  {STAGES[i][0]} -> {STAGES[i+1][0]};" for i in range(len(STAGES)-1)]
    lines.append("}")
    a.dot.parent.mkdir(parents=True,exist_ok=True);a.dot.write_text("\n".join(lines)+"\n",encoding="utf8")
    print(json.dumps({"dot":str(a.dot),"completed":[n for n,_ in STAGES if data.get(n) is True],
                      "remaining":[n for n,_ in STAGES if data.get(n) is not True]},ensure_ascii=False,indent=2))
    print("可选：dot -Tpng",a.dot,"-o pipeline.png")
if __name__=="__main__":main()
