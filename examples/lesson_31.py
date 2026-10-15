#!/usr/bin/env python3
"""第30讲专题2：对 YOLO 标注做实际质量检查，然后可用 Ultralytics 真正训练。"""
import argparse,json,sys
from pathlib import Path
def audit(root):
    files=list(root.rglob("*.txt"));bad=[];num=0
    for f in files:
        for lineno,line in enumerate(f.read_text(encoding="utf8").splitlines(),1):
            if not line.strip():continue
            parts=line.split()
            try:
                if len(parts)!=5:raise ValueError("expected 5 fields")
                cls=int(parts[0]);x,y,w,h=(float(z) for z in parts[1:])
                if cls<0 or not (0<=x<=1 and 0<=y<=1 and 0<w<=1 and 0<h<=1):
                    raise ValueError("invalid class or range")
                if x-w/2<0 or x+w/2>1 or y-h/2<0 or y+h/2>1:
                    raise ValueError("box outside image")
                num+=1
            except ValueError as exc:bad.append(f"{f}:{lineno}: {exc}")
    return {"label_files":len(files),"valid_boxes":num,"errors":bad}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--labels",type=Path,required=True);p.add_argument("--data",type=Path)
    p.add_argument("--epochs",type=int,default=10);p.add_argument("--weights",type=Path)
    p.add_argument("--train",action="store_true");p.add_argument("--report",type=Path,default=Path("build/lesson31/audit.json"))
    a=p.parse_args()
    if not a.labels.is_dir():p.error("labels directory missing")
    if a.epochs<1:p.error("epochs must be positive")
    result=audit(a.labels)
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if not result["label_files"] or result["errors"]:raise SystemExit("Invalid/empty label set; refusing to train")
    if a.train:
        if not a.data or not a.data.is_file() or not a.weights or not a.weights.is_file():
            p.error("Training requires real --data data.yaml and --weights .pt")
        from ultralytics import YOLO
        m=YOLO(str(a.weights));m.train(data=str(a.data),epochs=a.epochs)
        print("Real training finished. Save best.pt hash and independent validation metrics.")
if __name__=="__main__":main()
