#!/usr/bin/env python3
"""Prepare a REAL image tensor for RKNN/ONNX; choices must match the specific model.

No hidden defaults for model-dependent normalization. Default outputs uint8 RGB NHWC.
"""
import argparse
from pathlib import Path

def triplet(raw):
    vals=[float(v) for v in raw.split(",")]
    if len(vals)!=3:raise argparse.ArgumentTypeError("expected R,G,B as three numbers")
    return vals

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--image",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True,help="NumPy .npy output")
    ap.add_argument("--raw",type=Path,help="optional raw bytes for RKNPU2 C++ sample")
    ap.add_argument("--width",type=int,required=True)
    ap.add_argument("--height",type=int,required=True)
    ap.add_argument("--color",choices=("RGB","BGR"),default="RGB")
    ap.add_argument("--layout",choices=("NHWC","NCHW"),default="NHWC")
    ap.add_argument("--dtype",choices=("uint8","float32"),default="uint8")
    ap.add_argument("--scale",type=float,default=1.0,help="multiply source pixels before subtraction")
    ap.add_argument("--mean",type=triplet,default=[0.,0.,0.],help="per-channel after scaling")
    ap.add_argument("--std",type=triplet,default=[1.,1.,1.],help="per-channel divisors")
    args=ap.parse_args()
    if not args.image.is_file():ap.error("image file not found")
    if min(args.width,args.height)<=0:ap.error("width and height must be positive")
    if 0 in args.std:ap.error("std values must be nonzero")
    if args.dtype=="uint8" and (args.scale!=1 or args.mean!=[0.,0.,0.] or args.std!=[1.,1.,1.]):
        ap.error("For normalization, choose --dtype float32; uint8 must remain raw pixel bytes")
    import numpy as np
    from PIL import Image
    with Image.open(args.image) as img:
        arr=np.asarray(img.convert("RGB").resize((args.width,args.height),Image.Resampling.BILINEAR))
    if args.color=="BGR":arr=arr[...,::-1]
    if args.dtype=="float32":
        arr=arr.astype(np.float32)*args.scale
        arr=(arr-np.asarray(args.mean,np.float32))/np.asarray(args.std,np.float32)
    else:
        arr=np.ascontiguousarray(arr,np.uint8)
    if args.layout=="NCHW":
        arr=np.transpose(arr,(2,0,1))
    tensor=np.ascontiguousarray(arr[None,...])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    np.save(args.output,tensor)
    if args.raw:
        args.raw.parent.mkdir(parents=True,exist_ok=True)
        args.raw.write_bytes(tensor.tobytes(order="C"))
        print("Raw input:",args.raw,tensor.nbytes,"bytes")
    print("Tensor:",args.output,tensor.shape,tensor.dtype,
          "range:",float(tensor.min()),float(tensor.max()))
    print("WARNING: resizing, crop, color, layout and values must be verified against your model.")
if __name__=="__main__":
    main()
