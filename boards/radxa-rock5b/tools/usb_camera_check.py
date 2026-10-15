#!/usr/bin/env python3
"""Open a camera, capture real frames and optionally save one image. No AI inference."""
import argparse
import json
from pathlib import Path
import statistics
import sys
import time

def source_value(s):
    return int(s) if s.isdecimal() else s

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",default="/dev/video0",
                   help="V4L2 node, video index or OpenCV-compatible device source")
    p.add_argument("--frames",type=int,default=30)
    p.add_argument("--width",type=int,default=640)
    p.add_argument("--height",type=int,default=480)
    p.add_argument("--save-image",type=Path)
    p.add_argument("--save-json",type=Path)
    a=p.parse_args()
    if a.frames<2 or a.width<1 or a.height<1:
        p.error("frames>=2 and width/height>0 required")
    try:
        import cv2
    except ImportError:
        p.error("OpenCV missing; install python3-opencv / matching cv2 wheel")
    dev=source_value(a.source)
    cap=cv2.VideoCapture(dev,cv2.CAP_V4L2 if sys.platform.startswith("linux") else cv2.CAP_ANY)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open {a.source}; check USB camera, permissions and V4L2 node")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,a.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT,a.height)
    timestamps=[]
    shape=None
    try:
        for i in range(a.frames):
            ok,frame=cap.read()
            if not ok or frame is None:raise RuntimeError("Camera read failed at frame "+str(i))
            timestamps.append(time.monotonic())
            shape=list(frame.shape)
            if i==a.frames-1 and a.save_image:
                a.save_image.parent.mkdir(parents=True,exist_ok=True)
                if not cv2.imwrite(str(a.save_image),frame):
                    raise RuntimeError("Failed to save camera frame")
    finally:
        cap.release()
    intervals=[b-a for a,b in zip(timestamps,timestamps[1:])]
    report={"source":a.source,"frames":len(timestamps),"frame_shape":shape,
            "elapsed_seconds":round(timestamps[-1]-timestamps[0],4),
            "capture_fps":round((len(timestamps)-1)/(timestamps[-1]-timestamps[0]),3)
                 if timestamps[-1]>timestamps[0] else None,
            "mean_interframe_ms":round(statistics.mean(intervals)*1000,3),
            "note":"Frame capture only. NOT RK3588 NPU inference FPS."}
    if a.save_json:
        a.save_json.parent.mkdir(parents=True,exist_ok=True)
        a.save_json.write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
    print(json.dumps(report,indent=2))
    print("Camera images may contain people/private information; don't upload them without consent.")

if __name__=="__main__":
    try:main()
    except (RuntimeError,OSError) as exc:
        print("ERROR:",exc,file=sys.stderr)
        sys.exit(1)
