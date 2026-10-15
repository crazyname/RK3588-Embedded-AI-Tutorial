#!/usr/bin/env python3
"""第30讲专题1：用真实 Ultralytics checkpoint 预测图片，保存框信息与版本记录。"""
import argparse,json,sys,time
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--weights",type=Path,required=True);p.add_argument("--image",type=Path,required=True)
    p.add_argument("--imgsz",type=int,default=640);p.add_argument("--conf",type=float,default=.25)
    p.add_argument("--output",type=Path,default=Path("build/lesson30/predictions.json"));a=p.parse_args()
    if not a.weights.is_file() or not a.image.is_file():p.error("weights/image missing")
    if a.imgsz<1 or not 0<a.conf<=1:p.error("invalid imgsz/conf")
    import ultralytics
    from ultralytics import YOLO
    model=YOLO(str(a.weights))
    start=time.perf_counter();pred=model.predict(source=str(a.image),imgsz=a.imgsz,conf=a.conf,verbose=False)
    records=[]
    for x in pred:
        boxes=x.boxes
        records.append({"image":x.path,"xyxy":boxes.xyxy.cpu().numpy().tolist() if boxes is not None else [],
                        "confidence":boxes.conf.cpu().numpy().tolist() if boxes is not None else [],
                        "classes":boxes.cls.cpu().numpy().astype("int32").tolist() if boxes is not None else []})
    d={"ultralytics":ultralytics.__version__,"python":sys.version.split()[0],"weights":str(a.weights),
       "runtime_call_ms":(time.perf_counter()-start)*1000,"images":records}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
    print("Real prediction saved:",a.output,"boxes:",sum(len(z["xyxy"]) for z in records))
if __name__=="__main__":main()
