#!/usr/bin/env python3
"""Set up an isolated PC virtual environment. Dry run unless --apply is supplied."""
import argparse
from pathlib import Path
import platform
import subprocess
import sys
import venv

ROOT=Path(__file__).resolve().parents[1]
OPTIONS={"core":ROOT/"requirements/pc-core.txt","vision":ROOT/"requirements/pc-vision.txt"}

def python_in_venv(root):
    return root/"Scripts/python.exe" if platform.system()=="Windows" else root/"bin/python"

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--group",choices=OPTIONS.keys(),default="core")
    p.add_argument("--venv",type=Path,default=ROOT/".venv")
    p.add_argument("--apply",action="store_true",
                   help="Create virtual environment and install packages")
    a=p.parse_args()
    if not (3,10)<=sys.version_info[:2]<=(3,12):
        p.error("Use Python 3.10, 3.11 or 3.12 (CI uses 3.11)")
    location=a.venv.expanduser().resolve()
    req=OPTIONS[a.group]
    python=python_in_venv(location)
    print("Host:",platform.platform())
    print("Requirements:",req)
    print("Virtualenv:",location)
    print("Command:",python,"-m pip install -r",req)
    if not a.apply:
        print("DRY RUN: no files or packages changed. Add --apply to execute.")
        return
    if not location.is_dir():
        venv.EnvBuilder(with_pip=True).create(str(location))
    subprocess.run([str(python),"-m","pip","install","-r",str(req)],check=True)
    print("Environment ready. Run:",python,ROOT/"examples/lesson_00.py","--help")
if __name__=="__main__":
    main()
