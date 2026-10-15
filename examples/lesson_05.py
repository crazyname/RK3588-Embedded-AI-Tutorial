#!/usr/bin/env python3
"""第05讲：检查目标主机工具环境、Python ABI 和 RKNN-Toolkit2 安装状态。"""
import argparse,importlib.util,json,platform,sys,sysconfig,subprocess
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--require-toolkit",action="store_true")
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    spec=importlib.util.find_spec("rknn")
    d={"python":sys.version.split()[0],"executable":sys.executable,"abi":sysconfig.get_config_var("SOABI"),
       "machine":platform.machine(),"system":platform.system(),
       "venv":sys.prefix!=sys.base_prefix,"rknn_module_found":bool(spec)}
    if spec:
        try:
            from rknn.api import RKNN
            d["RKNN_class_imported"]=callable(RKNN)
        except Exception as exc:
            d["toolkit_import_error"]=str(exc);d["RKNN_class_imported"]=False
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2)+"\n")
    print(json.dumps(d,indent=2))
    if a.require_toolkit and not d.get("RKNN_class_imported",False):
        p.exit(2,"RKNN-Toolkit2 missing/incompatible. Check official wheel ABI and Python version.\n")
if __name__=="__main__":main()
