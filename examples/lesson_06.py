#!/usr/bin/env python3
"""第06讲：只读 NPU 设备/内核版本/Runtime ELF 检测，不执行驱动升级。"""
import argparse,json,os,platform,shutil,subprocess
from pathlib import Path
def read(path):
    try:return Path(path).read_text(errors="replace").strip()[:600]
    except (OSError,PermissionError):return None
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--runtime",type=Path,help="实际 librknnrt.so")
    p.add_argument("--output",type=Path)
    a=p.parse_args();data={"kernel":platform.release(),"machine":platform.machine(),
        "device_nodes":[str(x) for x in Path("/dev").glob("*rknpu*")] if Path("/dev").exists() else [],
        "runtime":None}
    if a.runtime:
        if not a.runtime.exists():p.error("runtime file missing")
        f={"path":str(a.runtime.resolve()),"bytes":a.runtime.stat().st_size}
        if shutil.which("file"):
            x=subprocess.run(["file",str(a.runtime)],text=True,capture_output=True,timeout=8)
            f["elf_description"]=x.stdout.strip()
        data["runtime"]=f
    for node in ("/sys/kernel/debug/rknpu/version","/sys/class/devfreq/fdab0000.npu/cur_freq"):
        value=read(node)
        if value is not None:data[node]=value
    s=json.dumps(data,indent=2,ensure_ascii=False)
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(s+"\n")
    print(s)
    print("此程序不会 insmod/刷写固件；版本兼容性需板商 BSP 和官方 SDK 确认。")
if __name__=="__main__":main()
