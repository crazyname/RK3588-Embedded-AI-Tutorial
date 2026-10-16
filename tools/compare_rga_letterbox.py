#!/usr/bin/env python3
"""Compare RGA letterbox RGB888 output against OpenCV on the SAME raw RGB frame.

This validates dimensions, pad placement, pixel errors, and source identity.
It cannot prove that a file was actually produced by the RGA hardware.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

def reference(raw,width,height,size=640):
    import cv2
    if min(width,height,size)<1:
        raise ValueError("Width, height and output size must be positive")
    pixels=np.asarray(raw,dtype=np.uint8)
    if pixels.size!=width*height*3:
        raise ValueError("Source is not packed RGB888 matching width*height*3")
    source=pixels.reshape((height,width,3))
    scale=min(size/width,size/height)
    # Python rounding is ties-to-even; C++ lround is ties-away-from-zero.
    new_w=max(1,min(size,int(np.floor(width*scale+.5))))
    new_h=max(1,min(size,int(np.floor(height*scale+.5))))
    x=(size-new_w)//2
    y=(size-new_h)//2
    resized=cv2.resize(source,(new_w,new_h),interpolation=cv2.INTER_LINEAR)
    out=np.zeros((size,size,3),dtype=np.uint8)
    out[y:y+new_h,x:x+new_w]=resized
    return out,{"left":x,"top":y,"width":new_w,"height":new_h}

def assess(source_bytes,result_bytes,width,height,max_mean_error=3.,size=640):
    if not 0<=max_mean_error<=255:
        raise ValueError("Invalid MAE acceptance threshold")
    expected,area=reference(np.frombuffer(source_bytes,dtype=np.uint8),width,height,size)
    if len(result_bytes)!=size*size*3:
        raise ValueError("Output file is not packed RGB888 output_size^2*3")
    actual=np.frombuffer(result_bytes,dtype=np.uint8).reshape((size,size,3))
    x,y,w,h=area["left"],area["top"],area["width"],area["height"]
    mask=np.zeros((size,size),dtype=bool)
    mask[y:y+h,x:x+w]=True
    if np.any(actual[~mask]):
        raise ValueError("Black letterbox padding contains nonzero pixels")
    diff=np.abs(actual[mask].astype(np.int16)-expected[mask].astype(np.int16))
    avg=float(np.mean(diff))
    result={"passed":avg<=max_mean_error,"width":width,"height":height,
            "output_size":size,"scale_x":w/width,"scale_y":h/height,
            "pad_x":x,"pad_y":y,
            "mean_abs_error_rgb":round(avg,4),
            "max_abs_error_rgb":int(np.max(diff)),
            "threshold_mae":max_mean_error,
            "note":"OpenCV-vs-file numerical comparison only. No proof that RGA ran."}
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input-rgb",type=Path,required=True)
    ap.add_argument("--rga-rgb",type=Path,required=True)
    ap.add_argument("--width",type=int,required=True)
    ap.add_argument("--height",type=int,required=True)
    ap.add_argument("--output-size",type=int,default=640)
    ap.add_argument("--max-mean-error",type=float,default=3.)
    args=ap.parse_args()
    try:
        source=args.input_rgb.read_bytes()
        result=args.rga_rgb.read_bytes()
        data=assess(source,result,args.width,args.height,
                    args.max_mean_error,args.output_size)
        data["input_sha256"]=hashlib.sha256(source).hexdigest()
        data["result_sha256"]=hashlib.sha256(result).hexdigest()
        print(json.dumps(data,indent=2,ensure_ascii=False))
        return 0 if data["passed"] else 1
    except (OSError,ValueError) as exc:
        print("INVALID:",exc)
        return 2
if __name__=="__main__":
    raise SystemExit(main())
