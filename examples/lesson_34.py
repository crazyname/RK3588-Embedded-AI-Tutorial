#!/usr/bin/env python3
"""第32讲：在 RK3588 真正调用 RKLLM 官方演示程序，捕获非伪造生成文本和墙钟时间。"""
import argparse,json,subprocess,time
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--program",type=Path,required=True,help="Actual RKLLM example executable")
    p.add_argument("--model",type=Path,required=True,help="Converted real RKLLM model")
    p.add_argument("--prompt",required=True);p.add_argument("--timeout",type=int,default=120)
    p.add_argument("--output",type=Path,default=Path("build/lesson34/rkllm_run.json"))
    p.add_argument("--model-arg",action="append",default=[],help="Additional exact official CLI args")
    a=p.parse_args()
    if not a.program.is_file() or not a.model.is_file():p.error("real RKLLM demo/model required")
    if a.timeout<1 or not a.prompt.strip():p.error("valid prompt and timeout required")
    # The exact official demo CLI differs across releases; simple demo convention:
    # executable <model_path>. Prompt is provided via stdin, never as shell commands.
    cmd=[str(a.program.resolve()),str(a.model.resolve()),*a.model_arg]
    t0=time.perf_counter()
    try:
        result=subprocess.run(cmd,input=a.prompt+"\n",capture_output=True,text=True,timeout=a.timeout)
    except subprocess.TimeoutExpired:raise SystemExit("RKLLM demo timeout")
    wall=time.perf_counter()-t0
    data={"program":cmd,"prompt":a.prompt,"returncode":result.returncode,"stdout":result.stdout,
          "stderr":result.stderr,"wall_seconds":wall,
          "note":"Wall time includes model loading; TTFT/tokens-s not inferred from an uninstrumented CLI"}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
    print("RKLLM subprocess log saved:",a.output,"exit:",result.returncode)
    if result.returncode:raise SystemExit(result.returncode)
if __name__=="__main__":main()
