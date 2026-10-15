#!/usr/bin/env python3
"""第28讲：封装可复用的 ONNX MobileNet 分类类，包含批图片、结果 JSON 与错误检查。"""
import argparse,json,time
from pathlib import Path
class MobileNetClassifier:
    def __init__(self,model,labels,width=224,height=224):
        import onnxruntime as ort
        self.session=ort.InferenceSession(str(model),providers=["CPUExecutionProvider"])
        specs=self.session.get_inputs()
        if len(specs)!=1:raise ValueError("This example supports one-input classifiers")
        self.input_name=specs[0].name
        self.width,self.height=width,height
        self.labels=[line.strip() for line in labels.read_text(encoding="utf-8-sig").splitlines()] if labels else None
    def predict(self,image,topk=5):
        import numpy as np
        from PIL import Image
        with Image.open(image) as im:
            a=np.asarray(im.convert("RGB").resize((self.width,self.height)),dtype=np.float32)/255.
        a=(a-np.array([.485,.456,.406],np.float32))/np.array([.229,.224,.225],np.float32)
        x=np.ascontiguousarray(a.transpose(2,0,1)[None,...])
        begin=time.perf_counter();out=self.session.run(None,{self.input_name:x})
        dt=(time.perf_counter()-begin)*1000
        if len(out)!=1:raise ValueError("Expected one classifier output")
        values=np.asarray(out[0]).reshape(-1).astype(np.float64)
        if self.labels and len(self.labels)!=len(values):raise ValueError("Label count mismatch")
        vals=np.exp(values-values.max());vals/=vals.sum()
        indices=np.argsort(-vals,kind="stable")[:topk]
        return {"image":str(image),"inference_call_ms":dt,
          "topk":[{"index":int(i),"probability":float(vals[i]),
                   "label":self.labels[i] if self.labels else str(int(i))} for i in indices]}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--onnx",type=Path,required=True)
    p.add_argument("--images",nargs="+",type=Path,required=True);p.add_argument("--labels",type=Path)
    p.add_argument("--width",type=int,default=224);p.add_argument("--height",type=int,default=224)
    p.add_argument("--topk",type=int,default=5);p.add_argument("--output",type=Path,default=Path("build/lesson28/results.json"))
    a=p.parse_args()
    if not a.onnx.is_file() or any(not f.is_file() for f in a.images):p.error("real model and images required")
    if a.labels and not a.labels.is_file():p.error("label file missing")
    if min(a.width,a.height,a.topk)<=0:p.error("positive width/height/topk required")
    app=MobileNetClassifier(a.onnx,a.labels,a.width,a.height)
    result=[app.predict(im,a.topk) for im in a.images]
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=="__main__":main()
