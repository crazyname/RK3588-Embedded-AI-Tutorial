#!/usr/bin/env python3
"""第08讲：真正调用外部 RKNN Model Zoo Demo，并保存 stdout/stderr/返回码。"""
import argparse,json,subprocess,time
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--program",type=Path,required=True,help="实际构建的 rknn_mobilenet_demo 等可执行文件")
    p.add_argument("--model",type=Path,required=True);p.add_argument("--image",type=Path,required=True)
    p.add_argument("--timeout",type=int,default=120);p.add_argument("--output",type=Path,default=Path("build/lesson08/result.json"))
    a=p.parse_args()
    for f in (a.program,a.model,a.image):
        if not f.is_file():p.error(f"missing file: {f}")
    if a.timeout<1:p.error("timeout must be positive")
    cmd=[str(a.program.resolve()),str(a.model.resolve()),str(a.image.resolve())]
    start=time.perf_counter()
    try:
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=a.timeout)
        status=r.returncode;stdout=r.stdout;stderr=r.stderr
    except subprocess.TimeoutExpired as exc:
        status=124;stdout=str(exc.stdout or b"");stderr="timeout: "+str(exc)
    result={"command":cmd,"exit_code":status,"seconds":time.perf_counter()-start,
            "stdout":stdout,"stderr":stderr,"is_real_external_execution":True}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("Saved",a.output,"exit code",status)
    if status:raise SystemExit(status if 0<status<126 else 1)
if __name__=="__main__":main()
