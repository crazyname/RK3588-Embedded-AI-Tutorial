#!/usr/bin/env python3
"""ROCK 5B on-device MobileNet image classification with REAL RKNNLite inference.

The input path is intentionally explicit: a compatible model should expect an
unsigned 8-bit RGB NHWC image. Normalization was included when compiling RKNN.
Always compare against the exact upstream Model Zoo version on a real board.
"""
import argparse
import json
from pathlib import Path
import sys
import time

def make_input(image, size, resize_mode):
    import numpy as np
    from PIL import Image, ImageOps
    with Image.open(image) as im:
        rgb=im.convert("RGB")
        if resize_mode=="center-crop":
            rgb=ImageOps.fit(rgb,size,method=Image.Resampling.BILINEAR,
                             centering=(.5,.5))
        else:
            rgb=rgb.resize(size,resample=Image.Resampling.BILINEAR)
        return np.ascontiguousarray(np.asarray(rgb,dtype=np.uint8))

def load_labels(path):
    if not path:return None
    return [row.strip() for row in path.read_text(encoding="utf-8").splitlines()]

def topk_scores(output, k):
    import numpy as np
    v=np.asarray(output).squeeze()
    if v.ndim!=1:
        raise ValueError(f"Expected a one-dimensional classifier output; got shape {v.shape}")
    if not np.issubdtype(v.dtype,np.number):
        raise ValueError(f"Output is not numeric: {v.dtype}")
    top=np.argsort(v)[::-1][:k]
    return [(int(i),float(v[i])) for i in top],int(v.size)

def run(model,input_tensor,runs,warmup):
    from rknnlite.api import RKNNLite
    sdk=RKNNLite()
    try:
        rc=sdk.load_rknn(str(model))
        if rc!=0:raise RuntimeError(f"RKNNLite.load_rknn error={rc}")
        rc=sdk.init_runtime()
        if rc!=0:raise RuntimeError(f"RKNNLite.init_runtime error={rc}")
        for _ in range(warmup):
            if sdk.inference(inputs=[input_tensor]) is None:
                raise RuntimeError("warmup inference returned None")
        durations=[]
        output=None
        for _ in range(runs):
            t0=time.perf_counter_ns()
            result=sdk.inference(inputs=[input_tensor])
            durations.append((time.perf_counter_ns()-t0)/1e6)
            if result is None or len(result)!=1:
                raise RuntimeError("Expected exactly 1 classifier output")
            output=result[0]
        return output,durations
    finally:
        sdk.release()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model",type=Path,required=True)
    ap.add_argument("--image",type=Path,required=True)
    ap.add_argument("--labels",type=Path)
    ap.add_argument("--width",type=int,default=224)
    ap.add_argument("--height",type=int,default=224)
    ap.add_argument("--resize",choices=("stretch","center-crop"),default="stretch")
    ap.add_argument("--topk",type=int,default=5)
    ap.add_argument("--runs",type=int,default=10)
    ap.add_argument("--warmup",type=int,default=3)
    ap.add_argument("--json",type=Path)
    ap.add_argument("--confirm-rgb-uint8-nhwc",action="store_true",
                    help="Acknowledge actual RKNN input contract and built-in mean/std")
    a=ap.parse_args()
    if not a.confirm_rgb_uint8_nhwc:
        ap.error("Pass --confirm-rgb-uint8-nhwc ONLY after checking your MODEL's input contract")
    if min(a.width,a.height,a.topk,a.runs)<1 or a.warmup<0:
        ap.error("positive width/height/topk/runs and warmup>=0 required")
    for file in (a.model,a.image):
        if not file.is_file():ap.error(f"Missing file: {file}")
    if a.labels and not a.labels.is_file():ap.error("labels file missing")
    input_tensor=make_input(a.image,(a.width,a.height),a.resize)
    if input_tensor.shape!=(a.height,a.width,3):
        raise RuntimeError(f"Unexpected tensor: {input_tensor.shape}")
    print("Tensor sent to RKNNLite:",input_tensor.shape,input_tensor.dtype)
    output,times=run(a.model,input_tensor,a.runs,a.warmup)
    predicted,classes=topk_scores(output,a.topk)
    labels=load_labels(a.labels)
    results=[]
    for i,score in predicted:
        entry={"class_index":i,"model_score":score}
        if labels is not None and len(labels)==classes:
            entry["label"]=labels[i]
        results.append(entry)
    if labels is not None and len(labels)!=classes:
        print(f"WARNING: label entries {len(labels)} != output classes {classes}; displaying indices only",
              file=sys.stderr)
    report={"model":str(a.model),"image":str(a.image),
            "input_shape":[int(x) for x in input_tensor.shape],
            "input_dtype":str(input_tensor.dtype),"resize_mode":a.resize,
            "topk":results,"class_count":classes,
            "sdk_call_latency_mean_ms":sum(times)/len(times),
            "runs":a.runs,"warmup":a.warmup,
            "note":"Actual RKNNLite outputs if run on real board; not camera FPS; softmax not applied."}
    print(json.dumps(report,indent=2,ensure_ascii=False))
    if a.json:
        a.json.parent.mkdir(parents=True,exist_ok=True)
        a.json.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",
                          encoding="utf-8")

if __name__=="__main__":
    try:main()
    except (ValueError,RuntimeError,OSError,ImportError) as exc:
        print("ERROR:",exc,file=sys.stderr)
        sys.exit(1)
