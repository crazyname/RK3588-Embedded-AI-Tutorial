#!/usr/bin/env python3
"""第26讲：检查真实 RKNN 模型和 raw tensor，生成零拷贝接口验收元数据。"""
import argparse,hashlib,json,subprocess
from pathlib import Path
def digest(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(65536),b""):h.update(chunk)
    return h.hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model",type=Path,required=True);p.add_argument("--input-raw",type=Path,required=True)
    p.add_argument("--native-input-bytes",type=int,required=True,help="From rknn_query(native_input_attr).size_with_stride")
    p.add_argument("--output",type=Path,default=Path("build/lesson26/zero_copy_check.json"))
    a=p.parse_args()
    for f in (a.model,a.input_raw):
        if not f.is_file():p.error("missing file "+str(f))
    if a.native_input_bytes<1:p.error("native input bytes must be positive")
    payload=a.input_raw.stat().st_size
    info={"model":str(a.model),"model_sha256":digest(a.model),
          "tensor_sha256":digest(a.input_raw),"actual_bytes":payload,
          "native_size_with_stride":a.native_input_bytes,
          "compatible_byte_count":payload==a.native_input_bytes,
          "requirements":["rknn_query(native attr)","rknn_create_mem",
                          "rknn_set_io_mem","cache coherency","rknn_destroy_mem"]}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(info,indent=2)+"\n")
    print(json.dumps(info,indent=2))
    print("Only memory-layout preflight. Does NOT execute zero-copy inference.")
    if not info["compatible_byte_count"]:raise SystemExit(1)
if __name__=="__main__":main()
