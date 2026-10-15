#!/usr/bin/env python3
"""第07讲：采集 CPU/NPU/DDR 可见频率和温度时间序列，纯只读。"""
import argparse,csv,time
from pathlib import Path
def nodes():
    files=[]
    for root in (Path("/sys/devices/system/cpu"),Path("/sys/class/devfreq"),Path("/sys/class/thermal")):
        if not root.exists():continue
        for pat in ("**/scaling_cur_freq","**/cur_freq","**/temp"):
            files.extend(root.glob(pat))
    return sorted({p for p in files if p.is_file()})[:128]
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--samples",type=int,default=3)
    ap.add_argument("--interval",type=float,default=.2);ap.add_argument("--output",type=Path,default=Path("build/lesson07/frequency.csv"))
    a=ap.parse_args()
    if a.samples<1 or not 0<=a.interval<=60:ap.error("samples must be >=1; interval 0..60 seconds")
    paths=nodes();a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("w",newline="",encoding="utf8") as f:
        wr=csv.writer(f);wr.writerow(["unix_time","sysfs_path","raw_value"])
        for n in range(a.samples):
            now=time.time()
            for path in paths:
                try:wr.writerow([now,str(path),path.read_text(errors="replace").strip()])
                except (OSError,PermissionError):pass
            if n+1<a.samples:time.sleep(a.interval)
    print(f"Collected {a.samples} samples, {len(paths)} candidate read-only nodes. CSV: {a.output}")
    if not paths:print("当前系统不暴露这些 sysfs 频率节点，不能据此断言开发板不支持 NPU。")
if __name__=="__main__":main()
