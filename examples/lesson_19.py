#!/usr/bin/env python3
"""第19讲：从真实图片构建一个 Batch NHWC uint8 输入及逐图片映射。"""
import argparse,json
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--images",nargs="+",type=Path,required=True)
    p.add_argument("--width",type=int,default=224);p.add_argument("--height",type=int,default=224)
    p.add_argument("--batch",type=int,default=4);p.add_argument("--output",type=Path,default=Path("build/lesson19/batch.npy"))
    a=p.parse_args()
    if a.batch<1 or len(a.images)!=a.batch or min(a.width,a.height)<1:p.error("images count must equal --batch, and sizes positive")
    import numpy as np
    from PIL import Image
    rows=[]
    for img in a.images:
        if not img.is_file():p.error("Missing image: "+str(img))
        with Image.open(img) as im:rows.append(np.asarray(im.convert("RGB").resize((a.width,a.height))))
    batch=np.stack(rows,axis=0)
    a.output.parent.mkdir(parents=True,exist_ok=True);np.save(a.output,batch)
    mapping={"images":[str(x) for x in a.images],"shape":list(batch.shape),"dtype":str(batch.dtype)}
    a.output.with_suffix(".json").write_text(json.dumps(mapping,indent=2)+"\n")
    print(json.dumps(mapping,indent=2))
    print("Batch input assembly succeeded; whether RKNN accepts N>1 depends on the compiled model.")
if __name__=="__main__":main()
