#!/usr/bin/env python3
"""第26讲：检查输入 buffer 并编译执行真实 RKNPU2 零拷贝实例。

缺少 SDK/模型/真实开发板时，可执行 --native-input-bytes 进行预检，
但预检不代表已经调用 rknn_create_mem/rknn_set_io_mem。
"""
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
    p.add_argument("--native-input-bytes",type=int,help="从 SDK rknn_query native input attr 获取的 size_with_stride")
    p.add_argument("--execute",action="store_true",help="实际编译和执行 C++ zero-copy 例程")
    p.add_argument("--include",type=Path,help="目录，包含 rknn_api.h")
    p.add_argument("--library",type=Path,help="对应 RK3588 版本的 librknnrt.so")
    p.add_argument("--build-dir",type=Path,default=Path("build/lesson26"))
    p.add_argument("--runs",type=int,default=5)
    p.add_argument("--output",type=Path,default=Path("build/lesson26/zero_copy_check.json"))
    a=p.parse_args()
    for f in (a.model,a.input_raw):
        if not f.is_file():p.error(f"input missing: {f}")
    if a.runs<=0:p.error("runs must be positive")
    size=a.input_raw.stat().st_size
    status={"model":str(a.model),"model_sha256":digest(a.model),
            "tensor_sha256":digest(a.input_raw),"raw_bytes":size,
            "native_size_with_stride":a.native_input_bytes,
            "zero_copy_executed":False}
    if a.native_input_bytes is not None:
        if a.native_input_bytes<1:p.error("native size must be positive")
        status["preflight_ok"]=size==a.native_input_bytes
        if not status["preflight_ok"]:p.error("raw input size differs from SDK-reported native buffer size")
    if a.execute:
        if not a.include or not (a.include/"rknn_api.h").is_file():p.error("--include must contain rknn_api.h")
        if not a.library or not a.library.is_file():p.error("--library needs matching RK3588 librknnrt.so")
        source=Path(__file__).parent/"hardware"
        commands=[
            ["cmake","-S",str(source),"-B",str(a.build_dir),
             "-DRKNN_INCLUDE_DIR="+str(a.include.resolve()),
             "-DRKNN_LIB="+str(a.library.resolve())],
            ["cmake","--build",str(a.build_dir),"-j"],
            [str((a.build_dir/"rknn_zero_copy").resolve()),
             str(a.model.resolve()),str(a.input_raw.resolve()),str(a.runs)]]
        for command in commands:
            print("Executing:",*command,flush=True)
            r=subprocess.run(command)
            if r.returncode:raise SystemExit(f"zero-copy compile/runtime step failed ({r.returncode})")
        status["zero_copy_executed"]=True
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(status,ensure_ascii=False,indent=2))
    if not a.execute:print("Only preflight completed. Add --execute with real SDK paths for NPU inference.")
if __name__=="__main__":main()
