#!/usr/bin/env python3
"""第15讲：对真实外部可执行程序做暖机、延迟分布及失败检测。"""
import argparse,csv,math,statistics,subprocess,time
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--warmup",type=int,default=3);p.add_argument("--runs",type=int,default=30)
    p.add_argument("--timeout",type=float,default=60);p.add_argument("--csv",type=Path,default=Path("build/lesson15/latency.csv"))
    p.add_argument("command",nargs=argparse.REMAINDER,help="-- /path/to/real/demo arg1 ...")
    a=p.parse_args()
    if a.warmup<0 or a.runs<1 or a.timeout<=0:p.error("invalid timing parameters")
    cmd=a.command[1:] if a.command[:1]==["--"] else a.command
    if not cmd:p.error("Provide real command after --; no fabricated benchmark")
    timings=[];a.csv.parent.mkdir(parents=True,exist_ok=True)
    for i in range(a.warmup+a.runs):
        t0=time.perf_counter()
        try:r=subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=a.timeout)
        except subprocess.TimeoutExpired as exc:raise SystemExit("Timed out: "+str(exc))
        dt=(time.perf_counter()-t0)*1000
        if r.returncode:raise SystemExit(f"Process returned {r.returncode}: {r.stderr.decode(errors='replace')[:400]}")
        if i>=a.warmup:timings.append(dt)
    with a.csv.open("w",newline="") as f:
        w=csv.writer(f);w.writerow(["sample","wall_ms"])
        w.writerows(enumerate(timings,1))
    data=sorted(timings);p95=data[max(0,math.ceil(.95*len(data))-1)]
    print(f"runs={len(data)} p50={statistics.median(data):.3f}ms p95={p95:.3f}ms mean={statistics.mean(data):.3f}ms")
    print("Each sample includes external process startup; not isolated NPU execution.")
if __name__=="__main__":main()
