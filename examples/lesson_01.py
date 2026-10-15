#!/usr/bin/env python3
"""第01讲：只读检查 CPU/内存/板卡与系统信息，不猜测芯片型号。"""
import argparse,json,platform,os
from pathlib import Path
def read(path):
    try:return Path(path).read_bytes().replace(b"\0",b" ").decode("utf8","replace").strip()
    except (OSError,PermissionError):return None
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",type=Path)
    a=p.parse_args()
    result={"kernel":platform.release(),"machine":platform.machine(),"cpu_count":os.cpu_count(),
            "device_tree_model":read("/proc/device-tree/model"),
            "device_tree_compatible":read("/proc/device-tree/compatible"),
            "meminfo":(read("/proc/meminfo") or "").splitlines()[:5],
            "cpuinfo":(read("/proc/cpuinfo") or "").splitlines()[:22]}
    payload=json.dumps(result,ensure_ascii=False,indent=2)
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(payload+"\n",encoding="utf8")
    print(payload)
    if not result["device_tree_model"]:print("提示：此系统可能不是 Linux 开发板，不能据此确定 RK3588")
if __name__=="__main__":main()
