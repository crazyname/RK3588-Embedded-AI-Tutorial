#!/usr/bin/env python3
"""第25讲：用 CMake 真正编译并执行本仓库 RKNPU2 C++ 分类程序。"""
import argparse,subprocess
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--include",type=Path,required=True,help="directory containing rknn_api.h")
    p.add_argument("--library",type=Path,required=True,help="matching aarch64 librknnrt.so")
    p.add_argument("--model",type=Path,required=True);p.add_argument("--tensor",type=Path,required=True)
    p.add_argument("--build-dir",type=Path,default=Path("build/lesson25"))
    a=p.parse_args()
    for f in (a.include/"rknn_api.h",a.library,a.model,a.tensor):
        if not f.is_file():p.error("missing SDK/model/input: "+str(f))
    project=Path(__file__).parent/"hardware"
    commands=[
      ["cmake","-S",str(project),"-B",str(a.build_dir),
       "-DRKNN_INCLUDE_DIR="+str(a.include.resolve()),"-DRKNN_LIB="+str(a.library.resolve())],
      ["cmake","--build",str(a.build_dir),"-j"],
      [str((a.build_dir/"rknn_classifier").resolve()),str(a.model.resolve()),str(a.tensor.resolve())]]
    for cmd in commands:
        print("Running:",*cmd,flush=True)
        r=subprocess.run(cmd,check=False)
        if r.returncode:raise SystemExit(f"CMake/RKNN execution failed: {r.returncode}")
    print("Real SDK C API program finished; inspect its Top-K output and NPU driver logs.")
if __name__=="__main__":main()
