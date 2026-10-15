#!/usr/bin/env python3
"""第09讲：先校验 ONNX，再调用真正的 RKNN-Toolkit2 转换器。"""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
def digest(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(65536),b""):h.update(chunk)
    return h.hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--onnx",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    p.add_argument("--mean",default="0,0,0");p.add_argument("--std",default="1,1,1")
    p.add_argument("--quantize",action="store_true");p.add_argument("--dataset",type=Path)
    p.add_argument("--manifest",type=Path,default=Path("build/lesson09/build.json"))
    a=p.parse_args()
    if not a.onnx.is_file():p.error("ONNX file missing")
    try:
        import onnx
    except ImportError:p.error("pip install onnx before conversion")
    graph=onnx.load(str(a.onnx));onnx.checker.check_model(graph)
    converter=Path(__file__).parent/"hardware"/"convert_onnx.py"
    cmd=[sys.executable,str(converter),"--onnx",str(a.onnx),"--output",str(a.output),
         "--mean",a.mean,"--std",a.std]
    if a.quantize:
        if not a.dataset or not a.dataset.is_file():p.error("INT8 requires --dataset")
        cmd += ["--quantize","--dataset",str(a.dataset)]
    r=subprocess.run(cmd,text=True)
    if r.returncode:raise SystemExit(f"RKNN conversion failed with exit status {r.returncode}")
    if not a.output.is_file() or a.output.stat().st_size==0:raise SystemExit("RKNN output missing")
    record={"onnx":str(a.onnx),"source_sha256":digest(a.onnx),
            "rknn":str(a.output),"rknn_sha256":digest(a.output),
            "onnx_nodes":len(graph.graph.node),"mean":a.mean,"std":a.std,"quantized":a.quantize}
    a.manifest.parent.mkdir(parents=True,exist_ok=True);a.manifest.write_text(json.dumps(record,indent=2)+"\n")
    print("Manifest:",a.manifest)
if __name__=="__main__":main()
