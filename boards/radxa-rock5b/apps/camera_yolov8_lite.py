#!/usr/bin/env python3
"""Real ROCK 5B USB camera -> optimized Model Zoo YOLOv8 RKNNLite -> bounding boxes.

Protocol is the *Rockchip optimized* YOLOv8 9/6-output DFL head, NOT arbitrary
Ultralytics YOLOv8/YOLO26. A valid 80-class matching .rknn is required.
No mock inference or auto-downloading in this CLI; CI tests explicitly inject fakes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time
import numpy as np
from yolov8_rknn_postprocess import letterbox, decode, draw_detections

HERE=Path(__file__).resolve().parent
DEFAULT_LABELS=HERE.parent/"assets/coco80.txt"

def read_labels(path):
    lines=[x.strip() for x in path.read_text(encoding="utf8").splitlines()]
    if len(lines)!=80 or any(not x for x in lines):
        raise ValueError("Rockchip reference YOLOv8n model expects exactly 80 COCO labels")
    return lines

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def make_camera(source,width,height):
    try:import cv2
    except ImportError as exc:raise RuntimeError("OpenCV missing") from exc
    device=int(source) if str(source).isdecimal() else source
    camera=cv2.VideoCapture(device,cv2.CAP_V4L2 if sys.platform.startswith("linux") else cv2.CAP_ANY)
    if not camera.isOpened():
        camera.release()
        raise RuntimeError(f"Cannot open camera {source}. Check UVC, permissions and video node.")
    camera.set(cv2.CAP_PROP_FRAME_WIDTH,width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT,height)
    return camera

def make_rknn():
    try:from rknnlite.api import RKNNLite
    except ImportError as exc:raise RuntimeError("Install matching ARM64 RKNN-Toolkit-Lite2") from exc
    return RKNNLite()

def check_args(args):
    if not args.confirm_optimized_yolov8:
        raise ValueError("Pass --confirm-optimized-yolov8 only for Model Zoo DFL 9/6-output models")
    if args.size!=640:
        raise ValueError("First hardware baseline is specifically 640x640 Model Zoo YOLOv8")
    if min(args.frames,args.capture_width,args.capture_height,args.max_det)<1 or args.warmup<0:
        raise ValueError("Invalid frames/warmup/capture size/max_det")
    if not 0<=args.conf<=1 or not 0<args.iou<1:
        raise ValueError("Invalid confidence/IoU threshold")
    if not args.model.is_file() or args.model.stat().st_size==0:
        raise FileNotFoundError("Missing or empty RKNN model: "+str(args.model))
    if not args.labels.is_file():raise FileNotFoundError("COCO labels file missing")
    if args.output_image and args.output_image.suffix.lower() not in (".jpg",".jpeg",".png"):
        raise ValueError("--output-image must end with .jpg, .jpeg or .png")

def percentile(values,q):
    values=sorted(values)
    return round(values[max(0,int(np.ceil(len(values)*q))-1)],3)

def summary_times(values):
    if not values:raise ValueError("No frames to summarize")
    return {"mean_ms":round(statistics.mean(values),3),
            "p50_ms":round(statistics.median(values),3),
            "p95_ms":percentile(values,.95),
            "max_ms":round(max(values),3)}

def run_loop(camera,sdk,labels,args,writer=None,display=None):
    """Synchronous V4L2 / CPU preprocessing / RKNNLite inference / CPU postprocessing.

    All sources are real with CLI defaults. Tests can inject fakes explicitly.
    """
    timing={key:[] for key in ("capture_ms","preprocess_ms","inference_ms",
                              "postprocess_ms","render_ms","end_to_end_ms")}
    rows=[]
    last_annotated=None
    began=None
    finished=None
    for i in range(args.frames+args.warmup):
        t0=time.perf_counter_ns()
        ok,frame=camera.read()
        t1=time.perf_counter_ns()
        if not ok or frame is None:raise RuntimeError(f"UVC frame read failed at iteration {i}")
        rgb,meta=letterbox(frame,args.size)
        t2=time.perf_counter_ns()
        output=sdk.inference(inputs=[rgb])
        t3=time.perf_counter_ns()
        detections=decode(output,meta,size=args.size,num_classes=len(labels),
                          conf=args.conf,iou=args.iou,max_det=args.max_det)
        t4=time.perf_counter_ns()
        if i<args.warmup:continue
        if began is None:began=t0
        drawn=None
        if args.output_image or args.view or args.output_video:
            drawn=draw_detections(frame,detections,labels)
            last_annotated=drawn
            if writer is not None:writer.write(drawn)
            if display is not None and display(drawn) is False:
                # On user-requested interactive display, allow q to end early.
                stop=True
            else:stop=False
        else:stop=False
        t5=time.perf_counter_ns()
        row={"frame":len(rows)+1,"detections":[
               {**entry,"label":labels[entry["class_id"]]} for entry in detections],
             "capture_ms":round((t1-t0)/1e6,3),
             "preprocess_ms":round((t2-t1)/1e6,3),
             "inference_ms":round((t3-t2)/1e6,3),
             "postprocess_ms":round((t4-t3)/1e6,3),
             "render_ms":round((t5-t4)/1e6,3),
             "end_to_end_ms":round((t5-t0)/1e6,3)}
        rows.append(row)
        for key in timing:timing[key].append(row[key])
        finished=t5
        if stop:break
    if not rows:raise RuntimeError("No measured frames")
    duration=(finished-began)/1e9
    summary={"measured_frames":len(rows),"warmup_frames":args.warmup,
             "capture_to_detection_seconds":round(duration,4),
             "synchronous_fps":round(len(rows)/duration,3) if duration>0 else None,
             "input_contract":"RGB uint8 HWC 640x640 / black padded letterbox",
             "output_contract":"Model Zoo optimized 3 DFL heads, 9 or 6 float outputs",
             "timing":{k:summary_times(v) for k,v in timing.items()},
             "last_detections":rows[-1]["detections"],
             "total_detections":sum(len(x["detections"]) for x in rows),
             "note":"Synchronous capture, CPU pre/postprocess and RKNNLite wall times; NOT NPU-only FPS, not mAP."}
    return summary,rows,last_annotated

def execute(args,camera_factory=None,rknn_factory=None,video_factory=None,display=None):
    check_args(args)
    labels=read_labels(args.labels)
    sdk=None;camera=None;writer=None
    try:
        sdk=(rknn_factory or make_rknn)()
        result=sdk.load_rknn(str(args.model))
        if result!=0:raise RuntimeError(f"RKNNLite.load_rknn failed: {result}")
        result=sdk.init_runtime()
        if result!=0:raise RuntimeError(f"RKNNLite.init_runtime failed: {result}")
        camera=(camera_factory or make_camera)(args.source,args.capture_width,args.capture_height)
        if args.output_video:
            if video_factory:
                writer=video_factory(args.output_video,args.capture_width,args.capture_height)
            else:
                import cv2
                # Capture backend can ignore negotiated resolution. Determine actual dimensions via camera.
                w=int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
                h=int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
                if w<1 or h<1:raise RuntimeError("Camera video output dimensions unknown")
                args.output_video.parent.mkdir(parents=True,exist_ok=True)
                writer=cv2.VideoWriter(str(args.output_video),
                      cv2.VideoWriter_fourcc(*"MJPG"),15.,(w,h))
                if not writer.isOpened():
                    writer.release()
                    raise RuntimeError("Could not create MJPG .avi output")
        if args.view and display is None:
            import cv2
            def show(frame):
                cv2.imshow("RK3588 RKNN YOLOv8",frame)
                return cv2.waitKey(1)&0xFF != ord("q")
            display=show
        summary,rows,last=run_loop(camera,sdk,labels,args,writer,display)
    finally:
        if writer is not None:writer.release()
        if camera is not None:camera.release()
        if sdk is not None:sdk.release()
        if args.view and display is not None and display.__name__=="show":
            try:
                import cv2
                cv2.destroyAllWindows()
            except ImportError:pass
    summary.update({"backend":"RKNNLite","model_sha256":sha256(args.model),
                    "camera_source":str(args.source),"labels_source":str(args.labels),
                    "has_annotated_image":bool(args.output_image),
                    "has_video":bool(args.output_video)})
    # Model hash computed after release; source camera image is saved only by explicit opt-in.
    if args.output_image and last is not None:
        import cv2
        args.output_image.parent.mkdir(parents=True,exist_ok=True)
        if not cv2.imwrite(str(args.output_image),last):
            raise RuntimeError("Failed to write annotated image")
    if args.summary:
        args.summary.parent.mkdir(parents=True,exist_ok=True)
        args.summary.write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    if args.jsonl:
        args.jsonl.parent.mkdir(parents=True,exist_ok=True)
        with args.jsonl.open("w",encoding="utf8") as f:
            for row in rows:f.write(json.dumps(row,ensure_ascii=False)+"\n")
    return summary

def parse_args(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model",type=Path,required=True,help="Rockchip optimized YOLOv8n RKNN for RK3588")
    p.add_argument("--labels",type=Path,default=DEFAULT_LABELS)
    p.add_argument("--source",default="/dev/video0",help="USB V4L2 camera path or index")
    p.add_argument("--capture-width",type=int,default=640)
    p.add_argument("--capture-height",type=int,default=480)
    p.add_argument("--size",type=int,default=640,help="Model input dimension; baseline requires 640")
    p.add_argument("--frames",type=int,default=100)
    p.add_argument("--warmup",type=int,default=10)
    p.add_argument("--conf",type=float,default=.25)
    p.add_argument("--iou",type=float,default=.45)
    p.add_argument("--max-det",type=int,default=100)
    p.add_argument("--summary",type=Path,help="save benchmark summary to JSON")
    p.add_argument("--jsonl",type=Path,help="save frame detections/timings to JSONL")
    p.add_argument("--output-image",type=Path,help="explicit opt-in: save last annotated frame")
    p.add_argument("--output-video",type=Path,help="explicit opt-in: MJPG .avi; may contain people")
    p.add_argument("--view",action="store_true",help="open local GUI window; q stops")
    p.add_argument("--confirm-optimized-yolov8",action="store_true",
                   help="affirm model is Rockchip Model Zoo optimized 9/6 output DFL model")
    return p.parse_args(argv)

def main():
    args=parse_args()
    try:
        result=execute(args)
        print(json.dumps(result,indent=2,ensure_ascii=False))
        return 0
    except (ValueError,RuntimeError,ImportError,OSError) as exc:
        print("ERROR:",exc,file=sys.stderr)
        return 1
if __name__=="__main__":
    raise SystemExit(main())
