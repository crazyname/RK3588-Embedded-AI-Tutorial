#!/usr/bin/env python3
"""Validate saved camera MobileNet timing and output reports without an NPU.

Schema/threshold checks do not certify that the data came from actual RK3588 hardware.
For trusted hardware evidence, also provide a device log and matching model SHA256.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

STAGES=("capture_ms","preprocess_ms","inference_ms","end_to_end_ms")

def check_positive(value,label,allow_zero=False):
    if isinstance(value,bool) or not isinstance(value,(int,float)):
        raise ValueError(f"{label}: expected a number")
    if not math.isfinite(value) or (value<0 if allow_zero else value<=0):
        raise ValueError(f"{label}: invalid value {value}")
    return value

def validate_topk(items,class_count):
    if not isinstance(items,list) or not items:
        raise ValueError("Top-K list missing or empty")
    previous=math.inf
    seen=set()
    for entry in items:
        if not isinstance(entry,dict):raise ValueError("Top-K record must be an object")
        index=entry.get("class_index")
        if not isinstance(index,int) or isinstance(index,bool) or not 0<=index<class_count:
            raise ValueError("Invalid class index")
        if index in seen:raise ValueError("Duplicate class index")
        seen.add(index)
        score=entry.get("model_score")
        if isinstance(score,bool) or not isinstance(score,(int,float)) or not math.isfinite(score):
            raise ValueError("Top-K contains a non-finite model score")
        if score>previous+1e-7:raise ValueError("Top-K scores are not sorted")
        previous=score

def validate(summary,rows=None,model=None,min_fps=None,max_inference_p95=None):
    """Raise ValueError on invalid report, otherwise return concise gate result."""
    if not isinstance(summary,dict):raise ValueError("Summary must be a JSON object")
    if not str(summary.get("backend","")).startswith("RKNNLite"):
        raise ValueError("This validator only accepts RKNNLite camera summaries")
    digest=summary.get("model_sha256")
    if not isinstance(digest,str) or not re.fullmatch(r"[a-fA-F0-9]{64}",digest):
        raise ValueError("Missing model SHA256")
    if model is not None:
        if not model.is_file():raise ValueError("Model file does not exist")
        h=hashlib.sha256()
        with model.open("rb") as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b""):
                h.update(chunk)
        if h.hexdigest().lower()!=digest.lower():
            raise ValueError("Report model digest differs from local .rknn file")
    frames=summary.get("processed_frames")
    warmup=summary.get("warmup_frames")
    classes=summary.get("class_count")
    if not isinstance(frames,int) or frames<1:
        raise ValueError("No processed frames")
    if not isinstance(warmup,int) or warmup<0:
        raise ValueError("Invalid warmup count")
    if not isinstance(classes,int) or classes<1:
        raise ValueError("Invalid class count")
    if summary.get("input_dtype")!="uint8" or summary.get("input_color")!="RGB":
        raise ValueError("Input contract differs from MobileNet RGB uint8 example")
    if summary.get("no_frames_saved") is not True:
        raise ValueError("Expected privacy-preserving no-frame-save report")
    check_positive(summary.get("throughput_fps"),"throughput_fps")
    timing=summary.get("timing")
    if not isinstance(timing,dict):raise ValueError("Timing object missing")
    for stage in STAGES:
        data=timing.get(stage)
        if not isinstance(data,dict):raise ValueError("Missing stage "+stage)
        vals=[check_positive(data.get(k),stage+"."+k,allow_zero=True)
              for k in ("mean_ms","p50_ms","p95_ms","max_ms")]
        if not (vals[1]<=vals[2]+.001 and vals[2]<=vals[3]+.001):
            raise ValueError("Timing percentiles out of order: "+stage)
    validate_topk(summary.get("last_topk"),classes)
    if rows is not None:
        if len(rows)!=frames:raise ValueError("JSONL row count differs from processed frames")
        for i,row in enumerate(rows,1):
            if row.get("frame")!=i:raise ValueError("Frame index mismatch in JSONL")
            validate_topk(row.get("topk"),classes)
            for stage in STAGES:
                check_positive(row.get(stage),"frame."+stage,allow_zero=True)
        if rows[-1].get("topk")!=summary.get("last_topk"):
            raise ValueError("JSONL final Top-K differs from summary")
    if min_fps is not None:
        check_positive(min_fps,"minimum FPS")
        if summary["throughput_fps"]<min_fps:
            raise ValueError(f"Throughput below requested threshold: {min_fps}")
    if max_inference_p95 is not None:
        check_positive(max_inference_p95,"maximum p95 ms")
        if timing["inference_ms"]["p95_ms"]>max_inference_p95:
            raise ValueError(f"Inference p95 exceeds threshold: {max_inference_p95} ms")
    return {"passed":True,"frame_count":frames,
            "fps":summary["throughput_fps"],
            "inference_p95_ms":timing["inference_ms"]["p95_ms"],
            "model_sha256":digest,
            "hardware_verified":False,
            "note":"File integrity and numerical gates only; not independent proof of a genuine hardware run."}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--summary",type=Path,required=True)
    ap.add_argument("--jsonl",type=Path,help="optional per-frame JSONL")
    ap.add_argument("--model",type=Path,help="compare model SHA256 against actual file")
    ap.add_argument("--min-fps",type=float,help="optional task-specific threshold")
    ap.add_argument("--max-inference-p95-ms",type=float,help="optional task-specific threshold")
    args=ap.parse_args()
    try:
        summary=json.loads(args.summary.read_text(encoding="utf8"))
        rows=None
        if args.jsonl:
            rows=[json.loads(s) for s in args.jsonl.read_text(encoding="utf8").splitlines()]
        result=validate(summary,rows,args.model,args.min_fps,args.max_inference_p95_ms)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (ValueError,OSError) as exc:
        print("INVALID CAMERA RUN:",exc)
        return 2
if __name__=="__main__":
    raise SystemExit(main())
