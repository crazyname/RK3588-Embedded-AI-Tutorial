#!/usr/bin/env python3
"""第10讲：真实图像不同 mean/std、通道顺序的输入数值差异。"""
import argparse,json
from pathlib import Path
def triple(s):
    vals=[float(x) for x in s.split(",")]
    if len(vals)!=3:raise argparse.ArgumentTypeError("need 3 numbers")
    return vals
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--image",type=Path,required=True)
    p.add_argument("--height",type=int,default=224);p.add_argument("--width",type=int,default=224)
    p.add_argument("--mean",type=triple,default=[.485,.456,.406])
    p.add_argument("--std",type=triple,default=[.229,.224,.225])
    p.add_argument("--layout",choices=("NCHW","NHWC"),default="NCHW")
    p.add_argument("--output",type=Path,default=Path("build/lesson10/image.npy"))
    a=p.parse_args()
    if not a.image.is_file():p.error("image missing")
    if min(a.width,a.height)<=0 or any(v==0 for v in a.std):p.error("invalid dimensions or std")
    import numpy as np
    from PIL import Image
    with Image.open(a.image) as im:
        rgb=np.asarray(im.convert("RGB").resize((a.width,a.height)),dtype=np.uint8)
    normalized=(rgb.astype("float32")/255-np.asarray(a.mean,np.float32))/np.asarray(a.std,np.float32)
    if a.layout=="NCHW":normalized=normalized.transpose(2,0,1)
    t=np.ascontiguousarray(normalized[None,...])
    a.output.parent.mkdir(parents=True,exist_ok=True);np.save(a.output,t)
    result={"source":str(a.image),"rgb_pixel_00":rgb[0,0].tolist(),
            "normalized_channel_mean":(rgb.astype("float32")/255-np.array(a.mean))/np.array(a.std),
            "shape":list(t.shape),"dtype":str(t.dtype),"npy":str(a.output)}
    del result["normalized_channel_mean"]
    result["min_per_channel"]=t.min(axis=(0,2,3)).tolist() if a.layout=="NCHW" else t.min(axis=(0,1,2)).tolist()
    result["max_per_channel"]=t.max(axis=(0,2,3)).tolist() if a.layout=="NCHW" else t.max(axis=(0,1,2)).tolist()
    print(json.dumps(result,ensure_ascii=False,indent=2))
    print("WARNING: compare actual model training preprocessing; do not normalize twice.")
if __name__=="__main__":main()
