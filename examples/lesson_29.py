#!/usr/bin/env python3
"""第29讲：运行真实 YOLOv5 检测推理，支持 Ultralytics 框架和官方 RKNN 可执行 Demo。"""
import argparse,json,subprocess,time
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--engine",choices=("ultralytics","rknn-demo"),required=True)
    p.add_argument("--model",type=Path,required=True);p.add_argument("--image",type=Path,required=True)
    p.add_argument("--program",type=Path,help="For rknn-demo: matching Model Zoo Linux binary")
    p.add_argument("--conf",type=float,default=.25);p.add_argument("--iou",type=float,default=.45)
    p.add_argument("--output",type=Path,default=Path("build/lesson29/detections.json"))
    a=p.parse_args()
    if not a.image.is_file() or not a.model.is_file():p.error("Real model and image required")
    if not 0<a.conf<1 or not 0<a.iou<1:p.error("conf/iou must be in (0,1)")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    if a.engine=="ultralytics":
        from ultralytics import YOLO
        model=YOLO(str(a.model))
        start=time.perf_counter()
        result=model.predict(str(a.image),conf=a.conf,iou=a.iou,verbose=False)[0]
        runtime=(time.perf_counter()-start)*1000
        found=[]
        if result.boxes is not None:
            for xyxy,conf,cls in zip(result.boxes.xyxy.cpu().numpy(),
                                      result.boxes.conf.cpu().numpy(),
                                      result.boxes.cls.cpu().numpy()):
                found.append({"xyxy":[float(x) for x in xyxy],"confidence":float(conf),"class_id":int(cls)})
        data={"engine":a.engine,"image":str(a.image),"detections":found,"total_call_ms":runtime}
        annotated=a.output.with_suffix(".jpg")
        import cv2
        if not cv2.imwrite(str(annotated),result.plot()):raise RuntimeError("Cannot write annotated image")
        data["annotated"]=str(annotated)
    else:
        if not a.program or not a.program.is_file():p.error("--program required for real RKNN demo")
        cmd=[str(a.program.resolve()),str(a.model.resolve()),str(a.image.resolve())]
        start=time.perf_counter()
        r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=120)
        data={"engine":a.engine,"command":cmd,"exit_code":r.returncode,
              "stdout":r.stdout,"stderr":r.stderr,"wall_ms":(time.perf_counter()-start)*1000,
              "note":"output/boxes follow this exact official Demo; this wrapper does not invent decoding"}
    a.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
    print("Wrote",a.output)
    if data.get("exit_code",0):raise SystemExit(data["exit_code"])
if __name__=="__main__":main()
