#!/usr/bin/env python3
"""第16讲：对一个真实 Linux PID 取样 VmRSS/VmHWM，观察峰值与稳态。"""
import argparse,csv,time
from pathlib import Path
def collect(pid):
    path=Path(f"/proc/{pid}/status")
    if not path.is_file():raise RuntimeError("PID not found or /proc unavailable")
    data={}
    for row in path.read_text(errors="replace").splitlines():
        if row.startswith(("VmRSS:","VmHWM:","VmSize:")):
            k,v=row.split(":",1);data[k]=v.strip()
    return data
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--pid",type=int,required=True)
    p.add_argument("--samples",type=int,default=10);p.add_argument("--interval",type=float,default=.5)
    p.add_argument("--csv",type=Path,default=Path("build/lesson16/memory.csv"));a=p.parse_args()
    if a.pid<=0 or a.samples<=0 or a.interval<0:p.error("invalid args")
    a.csv.parent.mkdir(parents=True,exist_ok=True)
    with a.csv.open("w",newline="") as f:
        writer=csv.writer(f);writer.writerow(["time","pid","VmRSS","VmHWM","VmSize"])
        for i in range(a.samples):
            try:v=collect(a.pid)
            except (OSError,RuntimeError) as e:raise SystemExit(str(e))
            writer.writerow([time.time(),a.pid,v.get("VmRSS"),v.get("VmHWM"),v.get("VmSize")])
            if i+1<a.samples:time.sleep(a.interval)
    print("Saved observed Linux process memory to",a.csv)
    print("VmRSS does not equal total NPU/DDR usage; consult SDK memory profiler.")
if __name__=="__main__":main()
