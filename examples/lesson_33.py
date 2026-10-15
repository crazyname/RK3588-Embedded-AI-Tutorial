#!/usr/bin/env python3
"""第31讲：真实 YOLOv8 前后两版模型在相同图片上的时延与检测框数对比。"""
import argparse,json,statistics,time
from pathlib import Path
def evaluate(weights,images,conf,warmup):
    from ultralytics import YOLO
    model=YOLO(str(weights))
    tms=[];counts=[]
    for index,image in enumerate(images):
        start=time.perf_counter()
        output=model.predict(source=str(image),conf=conf,verbose=False)[0]
        ms=(time.perf_counter()-start)*1000
        if index>=warmup:
            tms.append(ms);counts.append(len(output.boxes) if output.boxes is not None else 0)
    return {"weights":str(weights),"runs":len(tms),"wall_ms":tms,"median_ms":statistics.median(tms),
            "mean_ms":statistics.mean(tms),"per_image_boxes":counts}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline",type=Path,required=True);p.add_argument("--optimized",type=Path,required=True)
    p.add_argument("--images",nargs="+",type=Path,required=True);p.add_argument("--conf",type=float,default=.25)
    p.add_argument("--warmup",type=int,default=1);p.add_argument("--output",type=Path,default=Path("build/lesson33/compare.json"))
    a=p.parse_args()
    if any(not x.is_file() for x in [a.baseline,a.optimized,*a.images]):p.error("real models and images required")
    if a.warmup<0 or len(a.images)<=a.warmup:p.error("need more images than warmup count")
    if not 0<a.conf<1:p.error("conf outside (0,1)")
    baseline=evaluate(a.baseline,a.images,a.conf,a.warmup)
    optimized=evaluate(a.optimized,a.images,a.conf,a.warmup)
    ratio=baseline["median_ms"]/optimized["median_ms"]
    results={"baseline":baseline,"optimized":optimized,"median_speed_ratio":ratio,
             "note":"end-to-end framework calls on CURRENT host, not RK3588 NPU; mAP requires labeled test dataset"}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n")
    print("Real performance comparison saved:",a.output,"ratio:",ratio)
if __name__=="__main__":main()
