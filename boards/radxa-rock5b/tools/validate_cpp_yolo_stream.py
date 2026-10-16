#!/usr/bin/env python3
"""Offline schema/coordinate/timing checks for C++ V4L2→RGA→RKNN YOLOv8 JSONL.

This checks recorded output integrity, NOT that a real board produced the log.
Use a separately captured board/driver/model/version log for provenance.
"""
import argparse
import json
import math
from pathlib import Path
import statistics
import sys

PHASES=("capture_ms","rga_plus_cpu_letterbox_ms","inference_and_decode_ms")

def number(value,name,minimum=0.0,maximum=None):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    if value<minimum or (maximum is not None and value>maximum):
        raise ValueError(f"{name} outside expected range")
    return float(value)

def parse_line(line):
    def unique(pairs):
        obj={}
        for key,value in pairs:
            if key in obj:raise ValueError(f"Duplicate JSON field: {key}")
            obj[key]=value
        return obj
    def invalid_constant(value):
        raise ValueError("Nonstandard JSON numeric value: "+value)
    return json.loads(line,object_pairs_hook=unique,parse_constant=invalid_constant)

def percentile(items,ratio):
    values=sorted(items)
    return values[max(0,int(math.ceil(ratio*len(values)))-1)]

def assess(path,width,height,expected_frames=None,min_detections=0,max_inference_p95=None):
    if width<=0 or height<=0 or min_detections<0:
        raise ValueError("Invalid dimensions or minimum detection count")
    if expected_frames is not None and expected_frames<1:
        raise ValueError("Expected frame count must be positive")
    if max_inference_p95 is not None:
        number(max_inference_p95,"max_inference_p95",minimum=0.000001)
    times={phase:[] for phase in PHASES}
    counts={}
    frames=0
    detections_total=0
    with path.open(encoding="utf8") as stream:
        for line_no,raw in enumerate(stream,1):
            if not raw.strip():raise ValueError(f"Blank line {line_no}")
            row=parse_line(raw)
            if not isinstance(row,dict):raise ValueError(f"Frame {line_no} must be an object")
            index=row.get("frame")
            if isinstance(index,bool) or not isinstance(index,int) or index!=frames+1:
                raise ValueError(f"Frame index must be consecutive from 1 at line {line_no}")
            frames+=1
            for phase in PHASES:
                times[phase].append(number(row.get(phase),phase))
            det=row.get("detections")
            if not isinstance(det,list):raise ValueError("Missing detections array")
            prev=float("inf")
            for hit in det:
                if not isinstance(hit,dict):raise ValueError("Detection must be an object")
                category=hit.get("class_id")
                if isinstance(category,bool) or not isinstance(category,int) or category<0 or category>79:
                    raise ValueError("Detection class_id must be an integer in COCO 0..79")
                score=number(hit.get("score"),"confidence",maximum=1)
                if score>prev+1e-6:raise ValueError("Detections must be sorted by decreasing confidence")
                prev=score
                coords=hit.get("xyxy")
                if not isinstance(coords,list) or len(coords)!=4:
                    raise ValueError("Each detection requires a 4-element xyxy list")
                x1,y1,x2,y2=(number(v,"xyxy",minimum=0) for v in coords)
                if not (x1<x2<=width and y1<y2<=height):
                    raise ValueError("Detection box must be inside original camera frame")
                counts[category]=counts.get(category,0)+1
                detections_total+=1
    if frames<1:raise ValueError("No frame records")
    if expected_frames is not None and frames!=expected_frames:
        raise ValueError(f"Expected {expected_frames} frames, saw {frames}")
    if detections_total<min_detections:
        raise ValueError("Too few detections for requested acceptance criterion")
    summary={"passed":True,"frames":frames,"detections":detections_total,
             "classes_seen":dict(sorted(counts.items())),
             "timing":{name:{
                 "mean_ms":round(statistics.mean(samples),3),
                 "p50_ms":round(statistics.median(samples),3),
                 "p95_ms":round(percentile(samples,.95),3),
                 "max_ms":round(max(samples),3)}
                 for name,samples in times.items()},
             "hardware_verified":False,
             "note":"JSONL structure and numerical thresholds only, not proof of physical V4L2/RGA/NPU execution"}
    if (max_inference_p95 is not None and
            summary["timing"]["inference_and_decode_ms"]["p95_ms"]>max_inference_p95):
        raise ValueError("Inference+decode p95 exceeds requested threshold")
    return summary

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--jsonl",type=Path,required=True)
    p.add_argument("--width",type=int,required=True)
    p.add_argument("--height",type=int,required=True)
    p.add_argument("--expected-frames",type=int)
    p.add_argument("--min-detections",type=int,default=0)
    p.add_argument("--max-inference-p95-ms",type=float)
    p.add_argument("--summary",type=Path,help="optional output JSON summary")
    args=p.parse_args()
    try:
        result=assess(args.jsonl,args.width,args.height,
                      args.expected_frames,args.min_detections,args.max_inference_p95_ms)
        if args.summary:
            args.summary.parent.mkdir(parents=True,exist_ok=True)
            args.summary.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError) as exc:
        print("INVALID C++ YOLOV8 LOG:",exc,file=sys.stderr)
        return 2
if __name__=="__main__":
    raise SystemExit(main())
