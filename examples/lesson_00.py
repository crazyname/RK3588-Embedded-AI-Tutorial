#!/usr/bin/env python3
"""第00讲：生成当前主机的可复现环境清单。Python >=3.9。"""
import argparse, json, os, platform, shutil, subprocess, sys, hashlib
from pathlib import Path
def command_version(cmd):
    location=shutil.which(cmd)
    if not location: return {"installed":False}
    try:
        r=subprocess.run([cmd,"--version"],capture_output=True,text=True,timeout=8)
        return {"installed":True,"path":location,"version":(r.stdout or r.stderr).strip()[:300]}
    except (OSError,subprocess.TimeoutExpired) as e: return {"installed":True,"error":str(e)}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",type=Path,default=Path("build/lesson00/environment.json"))
    p.add_argument("--model",type=Path,help="可选的实际模型文件，计算 SHA256")
    a=p.parse_args()
    info={"python":sys.version,"executable":sys.executable,"platform":platform.platform(),"architecture":platform.machine(),
          "processor":platform.processor(),"hostname":platform.node(),"cpu_count":os.cpu_count(),
          "virtualenv":sys.prefix!=sys.base_prefix,"tools":{s:command_version(s) for s in ("git","cmake","gcc")}}
    if a.model:
        if not a.model.is_file():p.error("model file not found")
        h=hashlib.sha256()
        with a.model.open("rb") as f:
            for b in iter(lambda:f.read(65536),b""):h.update(b)
        info["model"]={"path":str(a.model.resolve()),"sha256":h.hexdigest(),"bytes":a.model.stat().st_size}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(info,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print("Saved environment manifest:",a.output)
if __name__=="__main__": main()
