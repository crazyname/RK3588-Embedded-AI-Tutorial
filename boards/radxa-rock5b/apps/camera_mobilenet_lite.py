#!/usr/bin/env python3
"""ROCK 5B: USB UVC camera -> RGB preprocessing -> real RKNNLite MobileNet inference.

Requires matching .rknn, rknn-toolkit-lite2, runtime/driver, USB camera and NumPy/Pillow.
The model contract is RGB uint8 HWC (batch passed as a single RKNNLite input array)
with any required normalization compiled into the RKNN model. No fallback/mock inference
is used by this CLI. Unit tests explicitly inject simulated camera/runtime objects.
"""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time

import numpy as np
from PIL import Image, ImageOps
from mobilenet_image_lite import topk_scores, load_labels

def prepare_bgr_frame(frame, width, height, resize):
    """Convert OpenCV BGR uint8 HWC to model RGB uint8 HWC, with explicit resize policy."""
    if not isinstance(frame,np.ndarray) or frame.ndim!=3 or frame.shape[2]!=3:
        raise ValueError("Expected a BGR image with 3 channels from the capture device")
    if frame.dtype!=np.uint8 or min(frame.shape[:2])==0:
        raise ValueError("Expected nonempty uint8 BGR image")
    if width<1 or height<1:
        raise ValueError("Target dimensions must be positive")
    # Pillow expects RGB. OpenCV provides BGR; reverse channels into a contiguous array.
    rgb=np.ascontiguousarray(frame[:,:,::-1])
    image=Image.fromarray(rgb,mode="RGB")
    if resize=="center-crop":
        image=ImageOps.fit(image,(width,height),
                           method=Image.Resampling.BILINEAR,
                           centering=(.5,.5))
    elif resize=="stretch":
        image=image.resize((width,height),resample=Image.Resampling.BILINEAR)
    else:
        raise ValueError("Unknown resize policy: "+str(resize))
    array=np.ascontiguousarray(np.asarray(image,dtype=np.uint8))
    if array.shape!=(height,width,3):
        raise RuntimeError("Prepared tensor shape mismatch")
    return array

def timing_summary(values):
    if not values:
        raise ValueError("No timing samples")
    ordered=sorted(values)
    index=max(0,int(np.ceil(.95*len(ordered)))-1)
    return {"mean_ms":round(statistics.mean(values),3),
            "p50_ms":round(statistics.median(values),3),
            "p95_ms":round(ordered[index],3),
            "max_ms":round(ordered[-1],3)}

def run_stream(capture,sdk,frames,warmup,width,height,resize,topk,labels):
    """Testable real capture-to-inference loop (SDK/capture passed in)."""
    if frames<1 or warmup<0 or topk<1:
        raise ValueError("frames and topk must be >=1; warmup >=0")
    records=[]
    begun=None
    elapsed=None
    timings={"capture_ms":[],"preprocess_ms":[],"inference_ms":[],"end_to_end_ms":[]}
    classes=None
    for iteration in range(warmup+frames):
        t0=time.perf_counter_ns()
        ok,bgr=capture.read()
        t1=time.perf_counter_ns()
        if not ok or bgr is None:
            raise RuntimeError(f"Camera read failed at frame {iteration}; check device and V4L2")
        tensor=prepare_bgr_frame(bgr,width,height,resize)
        t2=time.perf_counter_ns()
        outputs=sdk.inference(inputs=[tensor])
        t3=time.perf_counter_ns()
        if outputs is None or len(outputs)!=1:
            raise RuntimeError("RKNNLite returned invalid output; expected one classifier tensor")
        predicted,num_classes=topk_scores(outputs[0],topk)
        if labels is not None and len(labels)!=num_classes:
            raise ValueError(f"Label count {len(labels)} != classifier output {num_classes}")
        if classes is None:classes=num_classes
        elif classes!=num_classes:raise RuntimeError("Output class count changed during the run")
        if iteration < warmup:
            continue
        if begun is None:begun=t0
        elapsed=t3-begun
        record={"frame":iteration-warmup+1,
                "topk":[{"class_index":i,"model_score":score,
                         **({"label":labels[i]} if labels is not None else {})}
                        for i,score in predicted],
                "capture_ms":round((t1-t0)/1e6,3),
                "preprocess_ms":round((t2-t1)/1e6,3),
                "inference_ms":round((t3-t2)/1e6,3),
                "end_to_end_ms":round((t3-t0)/1e6,3)}
        for name in timings:
            timings[name].append(record[name])
        records.append(record)
    seconds=elapsed/1e9 if elapsed is not None else 0.
    summary={"processed_frames":len(records),"warmup_frames":warmup,
             "capture_to_inference_seconds":round(seconds,4),
             "throughput_fps":round(len(records)/seconds,3) if seconds>0 else None,
             "class_count":classes,"input_layout":"HWC","input_dtype":"uint8",
             "input_color":"RGB","input_shape":[height,width,3],
             "resize_policy":resize,
             "timing":{key:timing_summary(v) for key,v in timings.items()},
             "last_topk":records[-1]["topk"],
             "limitations":"One synchronous USB capture + CPU Pillow preprocessing + RKNNLite SDK call. No display, camera queue latency, RGA or DMA zero-copy claim."}
    return summary,records

def create_camera(source,capture_width,capture_height):
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("OpenCV unavailable: install suitable python3-opencv for the board") from exc
    device=int(source) if str(source).isdecimal() else source
    cap=cv2.VideoCapture(device,cv2.CAP_V4L2 if sys.platform.startswith("linux") else cv2.CAP_ANY)
    if not cap.isOpened():
        cap.release()
        raise RuntimeError(f"Camera cannot open {source}; check USB/UVC, /dev/video* and access rights")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,capture_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT,capture_height)
    return cap

def real_rknn_factory():
    try:
        from rknnlite.api import RKNNLite
    except ImportError as exc:
        raise RuntimeError("Install board-compatible RKNN Toolkit Lite2 wheel") from exc
    return RKNNLite()

def model_sha256(path):
    digest=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(65536),b""):
            digest.update(chunk)
    return digest.hexdigest()

def execute(args,camera_factory=None,sdk_factory=None):
    """Manage camera and NPU runtime lifecycle. Tests may explicitly inject fakes."""
    if not args.confirm_rgb_uint8_nhwc:
        raise ValueError("Pass --confirm-rgb-uint8-nhwc only after verifying YOUR RKNN model")
    if min(args.frames,args.width,args.height,args.capture_width,args.capture_height,args.topk)<1:
        raise ValueError("Frame count/dimensions/topk must be positive")
    if args.warmup<0:raise ValueError("warmup must be nonnegative")
    if not args.model.is_file() or args.model.stat().st_size==0:
        raise FileNotFoundError("Missing or empty RKNN model: "+str(args.model))
    if args.labels and not args.labels.is_file():
        raise FileNotFoundError("Label file missing: "+str(args.labels))
    labels=load_labels(args.labels)
    cap=None
    sdk=None
    try:
        cap=(camera_factory or create_camera)(
            args.source,args.capture_width,args.capture_height)
        sdk=(sdk_factory or real_rknn_factory)()
        result=sdk.load_rknn(str(args.model))
        if result!=0:raise RuntimeError(f"RKNNLite.load_rknn failed: {result}")
        result=sdk.init_runtime()
        if result!=0:raise RuntimeError(f"RKNNLite.init_runtime failed: {result}")
        summary,rows=run_stream(cap,sdk,args.frames,args.warmup,
                                args.width,args.height,args.resize,args.topk,labels)
    finally:
        if sdk is not None:sdk.release()
        if cap is not None:cap.release()
    summary["model_sha256"]=model_sha256(args.model)
    summary["source"]=str(args.source)
    summary["backend"]="RKNNLite (hardware when run with real board/SDK)"
    summary["no_frames_saved"]=True
    if args.json:
        args.json.parent.mkdir(parents=True,exist_ok=True)
        args.json.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    if args.jsonl:
        args.jsonl.parent.mkdir(parents=True,exist_ok=True)
        with args.jsonl.open("w",encoding="utf8") as f:
            for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")
    return summary

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model",type=Path,required=True)
    p.add_argument("--source",default="/dev/video0",help="USB UVC V4L2 camera; e.g. /dev/video0")
    p.add_argument("--labels",type=Path)
    p.add_argument("--frames",type=int,default=60,help="number of measured frames, excluding warmup")
    p.add_argument("--warmup",type=int,default=5)
    p.add_argument("--capture-width",type=int,default=640)
    p.add_argument("--capture-height",type=int,default=480)
    p.add_argument("--width",type=int,default=224,help="model width")
    p.add_argument("--height",type=int,default=224,help="model height")
    p.add_argument("--resize",choices=("stretch","center-crop"),default="center-crop")
    p.add_argument("--topk",type=int,default=3)
    p.add_argument("--json",type=Path,help="summary JSON file")
    p.add_argument("--jsonl",type=Path,help="per-frame predictions and timing (no raw images)")
    p.add_argument("--confirm-rgb-uint8-nhwc",action="store_true")
    args=p.parse_args()
    try:
        summary=execute(args)
        print(json.dumps(summary,indent=2,ensure_ascii=False))
        print("Real camera predictions were processed; no images were saved.")
    except (OSError,RuntimeError,ValueError,ImportError,KeyboardInterrupt) as exc:
        print("ERROR:",exc,file=sys.stderr)
        return 1
    return 0
if __name__=="__main__":
    raise SystemExit(main())
