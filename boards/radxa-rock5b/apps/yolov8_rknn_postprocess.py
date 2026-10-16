#!/usr/bin/env python3
"""Pure NumPy postprocessing for Rockchip MODEL ZOO optimized YOLOv8 (not generic YOLOv8).

Reference protocol: 3 detection heads, each has DFL 64-channel box logits,
80 class-confidence channels, optionally 1-channel confidence-sum output.
Supports 9 outputs (box,cls,sum repeated) or 6 outputs (box,cls repeated).
Input: RGB uint8 HWC after black-padding letterbox. Results in source-image xyxy.
Only FP output tensors are supported; raw quantized output requires dequantization
by RKNNLite. This is NOT the Ultralytics default [1,84,8400] format.
"""
import numpy as np

def letterbox(frame, size=640):
    """BGR input -> contiguous RGB HWC, black padding and inverse mapping metadata."""
    import cv2
    if not isinstance(frame,np.ndarray) or frame.ndim!=3 or frame.shape[-1]!=3:
        raise ValueError("Camera frame must be BGR HWC with 3 channels")
    if frame.dtype!=np.uint8 or min(frame.shape[:2])==0:
        raise ValueError("Camera frame must be nonempty uint8")
    if size<=0 or size%32:
        raise ValueError("Model input size must be a positive multiple of 32")
    h,w=frame.shape[:2]
    ratio=min(size/w,size/h)
    new_w=max(1,min(size,int(round(w*ratio))))
    new_h=max(1,min(size,int(round(h*ratio))))
    left=(size-new_w)//2
    top=(size-new_h)//2
    img=cv2.resize(frame,(new_w,new_h),interpolation=cv2.INTER_LINEAR)
    canvas=np.zeros((size,size,3),dtype=np.uint8)
    canvas[top:top+new_h,left:left+new_w]=img
    rgb=cv2.cvtColor(canvas,cv2.COLOR_BGR2RGB)
    return np.ascontiguousarray(rgb), {"source_wh":(w,h),"scale_x":new_w/w,
                                      "scale_y":new_h/h,"pad_x":left,"pad_y":top}

def dfl(logits):
    """Convert [1,64,H,W] DFL logits to [1,4,H,W] distances using softmax/expectation."""
    logits=np.asarray(logits)
    if logits.ndim!=4 or logits.shape[0]!=1 or logits.shape[1]!=64:
        raise ValueError("Expected single-batch 64-channel DFL box tensor [1,64,H,W]")
    if logits.dtype.kind!="f" or not np.isfinite(logits).all():
        raise ValueError("DFL output must be finite dequantized float tensor")
    shape=(1,4,16,logits.shape[2],logits.shape[3])
    y=logits.astype(np.float32,copy=False).reshape(shape)
    y=y-np.max(y,axis=2,keepdims=True)
    exp=np.exp(y)
    probabilities=exp/np.sum(exp,axis=2,keepdims=True)
    weights=np.arange(16,dtype=np.float32).reshape(1,1,16,1,1)
    return np.sum(probabilities*weights,axis=2)

def branch_xyxy(box_logits,size):
    distance=dfl(box_logits)[0]
    _,h,w=distance.shape
    if h<=0 or w<=0 or size%h or size%w:
        raise ValueError("Grid dimensions must divide the model input size")
    stride_x=size/w
    stride_y=size/h
    gy,gx=np.meshgrid(np.arange(h,dtype=np.float32),
                      np.arange(w,dtype=np.float32),indexing="ij")
    x=gx+0.5;y=gy+0.5
    xyxy=np.stack(((x-distance[0])*stride_x,(y-distance[1])*stride_y,
                   (x+distance[2])*stride_x,(y+distance[3])*stride_y),axis=-1)
    return xyxy.reshape(-1,4)

def _shapes(outputs,num_classes):
    if not isinstance(outputs,(list,tuple)) or len(outputs) not in (6,9):
        raise ValueError("Expected 6 or 9 Model Zoo optimized YOLOv8 output tensors")
    n=len(outputs)//3
    prev_size=None
    for k in range(3):
        box=np.asarray(outputs[k*n])
        cls=np.asarray(outputs[k*n+1])
        if box.ndim!=4 or box.shape[0]!=1 or box.shape[1]!=64:
            raise ValueError(f"Head {k} DFL shape must be [1,64,H,W]; got {box.shape}")
        if cls.ndim!=4 or cls.shape!=(1,num_classes,box.shape[2],box.shape[3]):
            raise ValueError(f"Head {k} class channels/grid mismatch: {cls.shape}")
        if prev_size is not None and box.shape[-1]>=prev_size:
            raise ValueError("Detection head order must be high-to-low resolution")
        prev_size=box.shape[-1]
        if box.shape[-2]!=box.shape[-1]:
            raise ValueError("This tutorial supports square feature grids only")
        if cls.dtype.kind!="f" or not np.isfinite(cls).all():
            raise ValueError("Class score output must be finite float tensor")
        if n==3:
            aux=np.asarray(outputs[k*n+2])
            if aux.shape!=(1,1,box.shape[2],box.shape[3]):
                raise ValueError("Auxiliary class-confidence-sum tensor shape mismatch")
    return n

def nms(boxes,scores,iou_threshold,max_det):
    """Greedy NMS on xyxy arrays, return original indices sorted by score."""
    boxes=np.asarray(boxes,dtype=np.float32)
    scores=np.asarray(scores,dtype=np.float32)
    if boxes.ndim!=2 or boxes.shape[1]!=4 or scores.shape!=(len(boxes),):
        raise ValueError("Invalid NMS box/score shape")
    if not 0<iou_threshold<1 or max_det<1:
        raise ValueError("Invalid NMS IoU threshold/max detections")
    order=np.argsort(-scores,kind="stable")
    keep=[]
    areas=np.maximum(0,boxes[:,2]-boxes[:,0])*np.maximum(0,boxes[:,3]-boxes[:,1])
    while order.size and len(keep)<max_det:
        idx=int(order[0])
        keep.append(idx)
        rest=order[1:]
        if not rest.size:break
        lo=np.maximum(boxes[idx,:2],boxes[rest,:2])
        hi=np.minimum(boxes[idx,2:],boxes[rest,2:])
        wh=np.maximum(0,hi-lo)
        inter=wh[:,0]*wh[:,1]
        union=areas[idx]+areas[rest]-inter
        iou=np.divide(inter,union,out=np.zeros_like(inter),where=union>0)
        order=rest[iou<=iou_threshold]
    return np.array(keep,dtype=np.int64)

def decode(outputs,meta,size=640,num_classes=80,conf=0.25,iou=0.45,max_det=100):
    """List of detections with source-image xyxy, score and zero-based class_id."""
    if not 0<=conf<=1 or not 0<iou<1 or max_det<1 or num_classes<1:
        raise ValueError("Invalid thresholds or class count")
    spacing=_shapes(outputs,num_classes)
    w_src,h_src=meta["source_wh"]
    if not (w_src>0 and h_src>0 and meta["scale_x"]>0 and meta["scale_y"]>0):
        raise ValueError("Invalid letterbox mapping metadata")
    all_boxes=[];all_classes=[];all_scores=[]
    for head in range(3):
        base=head*spacing
        box=np.asarray(outputs[base]); cls=np.asarray(outputs[base+1])
        if size%box.shape[-1] or size%box.shape[-2]:
            raise ValueError("Model output grid is incompatible with input size")
        score_map=cls[0].transpose(1,2,0).reshape(-1,num_classes)
        classids=np.argmax(score_map,axis=1)
        scores=score_map[np.arange(len(score_map)),classids]
        mask=scores>=conf
        if not np.any(mask):continue
        coords=branch_xyxy(box,size)[mask]
        all_boxes.append(coords)
        all_scores.append(scores[mask].astype(np.float32))
        all_classes.append(classids[mask].astype(np.int64))
    if not all_boxes:return []
    boxes=np.concatenate(all_boxes)
    classes=np.concatenate(all_classes)
    scores=np.concatenate(all_scores)
    boxes[:,[0,2]]=(boxes[:,[0,2]]-meta["pad_x"])/meta["scale_x"]
    boxes[:,[1,3]]=(boxes[:,[1,3]]-meta["pad_y"])/meta["scale_y"]
    boxes[:,[0,2]]=np.clip(boxes[:,[0,2]],0,w_src)
    boxes[:,[1,3]]=np.clip(boxes[:,[1,3]],0,h_src)
    valid=(boxes[:,2]>boxes[:,0])&(boxes[:,3]>boxes[:,1])
    boxes=boxes[valid];classes=classes[valid];scores=scores[valid]
    selected=[]
    for cls in np.unique(classes):
        indices=np.where(classes==cls)[0]
        retained=nms(boxes[indices],scores[indices],iou,max_det)
        selected.extend(indices[retained].tolist())
    selected=sorted(selected,key=lambda idx:(-float(scores[idx]),int(classes[idx])))[:max_det]
    return [{"class_id":int(classes[k]),"score":float(scores[k]),
             "xyxy":[float(v) for v in boxes[k]]} for k in selected]

def draw_detections(frame,detections,labels):
    """Draw source-resolution boxes on BGR frame for optional local use."""
    import cv2
    shown=frame.copy()
    h,w=shown.shape[:2]
    for hit in detections:
        x1,y1,x2,y2=(int(round(v)) for v in hit["xyxy"])
        x1=max(0,min(w-1,x1));x2=max(0,min(w-1,x2))
        y1=max(0,min(h-1,y1));y2=max(0,min(h-1,y2))
        if x2<=x1 or y2<=y1:continue
        cls=hit["class_id"]
        title=f"{labels[cls]} {hit['score']:.2f}"
        cv2.rectangle(shown,(x1,y1),(x2,y2),(0,255,0),2)
        cv2.putText(shown,title,(x1,max(12,y1-6)),cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,(0,255,0),1,cv2.LINE_AA)
    return shown
