#!/usr/bin/env python3
"""第11讲：把真实 ONNX→RKNN 批量转换任务从 JSON 配置逐项执行并留下日志。"""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--jobs",type=Path,required=True,help='JSON: [{"onnx":"m.onnx","output":"m.rknn","mean":"0,0,0","std":"1,1,1"}]')
    p.add_argument("--log-dir",type=Path,default=Path("build/lesson11"))
    a=p.parse_args()
    if not a.jobs.is_file():p.error("jobs file missing")
    tasks=json.loads(a.jobs.read_text(encoding="utf8"))
    if not isinstance(tasks,list) or not tasks:p.error("jobs must be a non-empty JSON array")
    a.log_dir.mkdir(parents=True,exist_ok=True);results=[];bad=0
    for i,task in enumerate(tasks):
        if not isinstance(task,dict) or not all(k in task for k in ("onnx","output","mean","std")):
            p.error(f"jobs[{i}] missing fields")
        cmd=[sys.executable,str(Path(__file__).parent/"hardware"/"convert_onnx.py"),
             "--onnx",str(task["onnx"]),"--output",str(task["output"]),
             "--mean",str(task["mean"]),"--std",str(task["std"])]
        if task.get("quantize"):
            if not task.get("dataset"):p.error("Quantization requires dataset")
            cmd+=["--quantize","--dataset",str(task["dataset"])]
        result=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        log=a.log_dir/f"task_{i:02d}.log";log.write_text(result.stdout,encoding="utf8")
        results.append({"task":i,"exit_code":result.returncode,"output":task["output"],"log":str(log)})
        bad+=result.returncode!=0
    (a.log_dir/"manifest.json").write_text(json.dumps(results,indent=2)+"\n")
    print(json.dumps(results,indent=2))
    if bad:raise SystemExit(f"{bad}/{len(tasks)} conversions failed")
if __name__=="__main__":main()
