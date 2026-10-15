#!/usr/bin/env python3
"""Real Ultralytics PyTorch -> ONNX export and ONNX validity check."""
import argparse
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--weights",type=Path,required=True)
    ap.add_argument("--imgsz",type=int,default=640)
    ap.add_argument("--opset",type=int,default=0)
    a=ap.parse_args()
    if not a.weights.is_file():ap.error("Checkpoint not found")
    if a.imgsz<1:ap.error("imgsz must be positive")
    from ultralytics import YOLO
    import onnx
    kw={"format":"onnx","imgsz":a.imgsz,"dynamic":False}
    if a.opset:kw["opset"]=a.opset
    out=Path(YOLO(str(a.weights)).export(**kw))
    onnx.checker.check_model(onnx.load(str(out)))
    print("Verified ONNX:",out)
    print("NEXT: test ONNX Runtime. RKNN compatibility is NOT guaranteed.")
if __name__=="__main__":
    main()
