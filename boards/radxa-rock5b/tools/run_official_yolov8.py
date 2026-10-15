#!/usr/bin/env python3
"""Run Radxa OS packaged RKNN Model Zoo YOLOv8 reference demo (not a reimplementation).

Requires Radxa OS package rknn-model-zoo-rk3588 and compatible RK3588 Runtime.
Never uses sudo automatically. Will not download/flash anything.
"""
import argparse
from pathlib import Path
import subprocess
import sys

DEFAULT_ROOT=Path("/usr/share/rknn_model_zoo/examples/yolov8")
def command_for(root,python,images,save):
    script=root/"python"/"yolov8.py"
    model=root/"model"/"yolov8.rknn"
    if not script.is_file():
        raise FileNotFoundError(f"Missing vendor example {script}. Check official package.")
    if not model.is_file():
        raise FileNotFoundError(f"Missing vendor RKNN model {model}. Check official package.")
    cmd=[python,str(script),"--model_path",str(model)]
    if images:
        if not images.is_dir():
            raise FileNotFoundError(f"Image folder not found: {images}")
        cmd.extend(["--img_folder",str(images.resolve())])
    if save:cmd.append("--img_save")
    return cmd,script.parent

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--example-root",type=Path,default=DEFAULT_ROOT)
    ap.add_argument("--python",default=sys.executable)
    ap.add_argument("--images",type=Path,help="optional test image directory")
    ap.add_argument("--save",action="store_true")
    ap.add_argument("--dry-run",action="store_true",
                    help="check vendor files & print exact command, no inference")
    a=ap.parse_args()
    cmd,cwd=command_for(a.example_root,a.python,a.images,a.save)
    print("Working directory:",cwd,flush=True)
    print("Command arguments:",cmd,flush=True)
    if a.dry_run:return
    print("Running vendor sample without automatic privilege escalation...",flush=True)
    subprocess.run(cmd,cwd=cwd,check=True)
    print("Success: command exited 0; inspect stdout, saved image and actual detections.")

if __name__=="__main__":
    try:main()
    except (OSError,subprocess.CalledProcessError) as e:
        print("ERROR:",e,file=sys.stderr)
        sys.exit(1)
