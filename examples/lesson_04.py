#!/usr/bin/env python3
"""第04讲：通过 Git CLI 核实官方仓库远端引用并生成可追溯记录。"""
import argparse,json,shutil,subprocess
from pathlib import Path
REPOS={"toolkit2":"https://github.com/airockchip/rknn-toolkit2.git",
       "model_zoo":"https://github.com/airockchip/rknn_model_zoo.git",
       "rknpu2":"https://github.com/rockchip-linux/rknpu2.git",
       "rkllm":"https://github.com/airockchip/rknn-llm.git"}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--repo",choices=list(REPOS),required=True)
    p.add_argument("--ref",default="HEAD");p.add_argument("--output",type=Path)
    a=p.parse_args()
    if not shutil.which("git"):p.error("git not found")
    url=REPOS[a.repo]
    try:
        done=subprocess.run(["git","ls-remote",url,a.ref],capture_output=True,text=True,timeout=35)
    except subprocess.TimeoutExpired:p.error("git ls-remote timed out; check network")
    if done.returncode:p.error((done.stderr or "git ls-remote failed").strip()[:500])
    refs=[dict(zip(("sha","ref"),line.split("\t",1))) for line in done.stdout.strip().splitlines() if "\t" in line]
    if not refs:p.error("no refs found; check --ref")
    data={"repository":url,"requested_ref":a.ref,"resolved":refs}
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(data,indent=2)+"\n")
    print(json.dumps(data,indent=2))
if __name__=="__main__":main()
