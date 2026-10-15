#!/usr/bin/env python3
"""第30讲专题3：从已有 checkpoint 真实导出 ONNX、检查图、可选尝试 RKNN 编译。"""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda:f.read(65536),b""):h.update(block)
    return h.hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--weights",type=Path,required=True)
    p.add_argument("--imgsz",type=int,default=640);p.add_argument("--rknn",type=Path)
    p.add_argument("--mean",default="0,0,0");p.add_argument("--std",default="255,255,255")
    p.add_argument("--report",type=Path,default=Path("build/lesson32/conversion.json"));a=p.parse_args()
    if not a.weights.is_file() or a.imgsz<=0:p.error("real checkpoint and positive size required")
    import onnx
    from ultralytics import YOLO
    exported=Path(YOLO(str(a.weights)).export(format="onnx",imgsz=a.imgsz,dynamic=False))
    model=onnx.load(str(exported));onnx.checker.check_model(model)
    result={"weights":str(a.weights),"weights_sha":sha(a.weights),
            "onnx":str(exported),"onnx_sha":sha(exported),"onnx_nodes":len(model.graph.node),
            "rknn_status":"not requested"}
    if a.rknn:
        cmd=[sys.executable,str(Path(__file__).parent/"hardware"/"convert_onnx.py"),
            "--onnx",str(exported),"--output",str(a.rknn),"--mean",a.mean,"--std",a.std]
        r=subprocess.run(cmd)
        result["rknn_status"]="success" if r.returncode==0 else f"failed exit={r.returncode}"
        if r.returncode==0 and a.rknn.is_file():result["rknn_sha"]=sha(a.rknn)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if a.rknn and result["rknn_status"]!="success":raise SystemExit("RKNN conversion failed")
    print("ONNX export and conversion alone do not prove RK3588 detection head postprocessing.")
if __name__=="__main__":main()
