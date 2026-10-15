#!/usr/bin/env python3
"""第23讲：从真实 ONNX 模型生成有输入/输出形状定义的可编译 C++ 接口描述。"""
import argparse,re,subprocess
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--onnx",type=Path,required=True)
    p.add_argument("--output",type=Path,default=Path("build/lesson23/tensors.hpp"))
    p.add_argument("--compile",action="store_true",help="Use g++ to syntax check generated header")
    a=p.parse_args()
    if not a.onnx.is_file():p.error("ONNX file missing")
    import onnx
    m=onnx.load(str(a.onnx));onnx.checker.check_model(m)
    values=list(m.graph.input)+list(m.graph.output)
    lines=["#pragma once","#include <array>","#include <cstdint>","#include <string_view>",
           "namespace generated_model {","struct TensorDescription {std::string_view name; std::string_view dims; int dtype;};"]
    for i,v in enumerate(values):
        dims=[]
        for d in v.type.tensor_type.shape.dim:
            dims.append(str(d.dim_value) if d.HasField("dim_value") else (d.dim_param or "?"))
        lines.append(f"inline constexpr TensorDescription tensor_{i} = "
                     f'{{"{v.name.replace(chr(34),"_")}","{",".join(dims)}",{v.type.tensor_type.elem_type}}};')
    lines.append(f"inline constexpr int input_count={len(m.graph.input)};")
    lines.append(f"inline constexpr int output_count={len(m.graph.output)};")
    lines.append("}")
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text("\n".join(lines)+"\n",encoding="utf8")
    if a.compile:
        test=a.output.parent/"_compile_test.cpp";test.write_text(f'#include "{a.output.name}"\nint main(){{return generated_model::input_count<1;}}\n')
        r=subprocess.run(["g++","-std=c++17","-fsyntax-only",str(test)],capture_output=True,text=True)
        if r.returncode:raise SystemExit(r.stderr)
    print("Generated real-model tensor header",a.output)
    print("This file describes the graph interface, NOT a complete RKNN runtime implementation.")
if __name__=="__main__":main()
