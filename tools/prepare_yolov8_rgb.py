#!/usr/bin/env python3
"""Prepare EXACT 640x640 RGB uint8 black-letterbox RAW input for C++ RKNN YOLOv8.

Use the same Python processing implementation as the camera_yolov8_lite app.
No model download or NPU invocation; run from repository root with OpenCV/NumPy.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import cv2

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"boards/radxa-rock5b/apps"))
from yolov8_rknn_postprocess import letterbox

def prepare(image,out_raw,manifest):
    bgr=cv2.imread(str(image),cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("Image unreadable or missing: "+str(image))
    h,w=bgr.shape[:2]
    rgb,mapping=letterbox(bgr,640)
    raw=rgb.tobytes()
    if len(raw)!=640*640*3:raise ValueError("Bad RGB tensor length")
    out_raw.parent.mkdir(parents=True,exist_ok=True)
    out_raw.write_bytes(raw)
    detail={"source_image":str(image),"source_width":w,"source_height":h,
            "model_size":640,"model_input_format":"RGB uint8 HWC",
            "resize":"black letterbox, OpenCV bilinear",
            "raw_output":str(out_raw),
            "tensor_bytes":len(raw),"tensor_sha256":hashlib.sha256(raw).hexdigest(),
            "inverse_mapping":{key:(list(value) if isinstance(value,tuple) else value)
                               for key,value in mapping.items()},
            "note":"CPU preprocessing, not RGA or DMA-BUF. No claim of actual NPU inference."}
    if manifest:
        manifest.parent.mkdir(parents=True,exist_ok=True)
        manifest.write_text(json.dumps(detail,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    return detail

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--image",type=Path,required=True,help="local JPEG/PNG to preprocess")
    p.add_argument("--raw",type=Path,required=True,help="packed 640x640 RGB uint8 RAW output")
    p.add_argument("--manifest",type=Path,help="optional provenance and inverse-map JSON")
    a=p.parse_args()
    try:
        result=prepare(a.image,a.raw,a.manifest)
        print(json.dumps(result,indent=2,ensure_ascii=False))
        return 0
    except (ValueError,OSError) as exc:
        print("ERROR:",exc,file=sys.stderr)
        return 1

if __name__=="__main__":
    raise SystemExit(main())
