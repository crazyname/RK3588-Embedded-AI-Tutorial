#!/usr/bin/env python3
"""Read-only ROCK 5B hardware audit. No device writes, serial numbers or MAC addresses."""
import argparse
import json
import os
from pathlib import Path
import platform
import re
import sys

def read_text(path, maximum=4096):
    try:
        raw=Path(path).read_bytes()[:maximum]
        return raw.decode("utf-8","replace").replace("\x00"," ").strip()
    except (OSError, ValueError):
        return None

def is_rock5b(model, compatibles=()):
    """Original ROCK 5B only. ROCK 5B+ is a distinct hardware target."""
    name=(model or "").lower().strip()
    normal=re.sub(r"[^a-z0-9]+"," ",name).strip()
    if "5b plus" in normal or "5b+" in name or "5b+" in " ".join(compatibles):
        return False
    by_name=any(s in normal for s in ("rock 5b","rock 5 model b","rock5b"))
    compatibles=[str(c).lower() for c in compatibles]
    by_compat=any("radxa,rock-5b" in c or "radxa,rock5b" in c
                  for c in compatibles) and not any("plus" in c for c in compatibles)
    return by_name or by_compat

def read_compatibles():
    try:
        return [v.decode("utf-8","replace") for v in
                Path("/proc/device-tree/compatible").read_bytes().split(b"\0") if v]
    except OSError:
        return []

def os_release():
    data={}
    text=read_text("/etc/os-release") or ""
    for line in text.splitlines():
        if "=" not in line or line.startswith("#"):continue
        k,v=line.split("=",1)
        if k in {"NAME","VERSION_ID","VERSION_CODENAME","PRETTY_NAME"}:
            data[k]=v.strip('"')
    return data

def thermal_zones():
    result=[]
    for node in sorted(Path("/sys/class/thermal").glob("thermal_zone*"))[:24]:
        typ=read_text(node/"type")
        temp=read_text(node/"temp")
        try:
            c=round(float(temp)/1000,1) if temp is not None else None
        except ValueError:
            c=None
        if typ and c is not None:
            result.append({"sensor":typ,"celsius":c})
    return result

def npu_clues():
    found=[]
    for root in (Path("/sys/class/devfreq"),Path("/sys/devices/platform")):
        for p in sorted(root.glob("*npu*"))[:12]:
            found.append(str(p))
    modules=read_text("/proc/modules",maximum=250000) or ""
    if re.search(r"(?m)^rknpu\b",modules):
        found.append("rknpu kernel module loaded")
    return sorted(set(found))

def list_video():
    result=[]
    for p in sorted(Path("/dev").glob("video[0-9]*"))[:24]:
        name=read_text(Path("/sys/class/video4linux")/p.name/"name")
        result.append({"device":str(p),"driver_name":name or "unknown"})
    return result

def memtotal_kib():
    text=read_text("/proc/meminfo") or ""
    m=re.search(r"(?m)^MemTotal:\s+(\d+)\s+kB",text)
    return int(m.group(1)) if m else None

def build_report():
    model=read_text("/proc/device-tree/model")
    comp=read_compatibles()
    return {
        "target":"Radxa ROCK 5B (not 5B+)",
        "board_model":model,
        "compatible":comp,
        "matches_rock5b":is_rock5b(model,comp),
        "architecture":platform.machine(),
        "kernel":platform.release(),
        "os":os_release(),
        "python":platform.python_version(),
        "memory_kib":memtotal_kib(),
        "npu_evidence":npu_clues(),
        "thermal_celsius":thermal_zones(),
        "video_nodes":list_video(),
        "note":"Presence of nodes is not proof RKNN runtime/driver/model compatibility. No secrets or unique serials collected."
    }

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output",type=Path,help="optional JSON output file")
    ap.add_argument("--strict",action="store_true",
                    help="fail if device-tree does not identify original ROCK 5B")
    a=ap.parse_args()
    result=build_report()
    rendered=json.dumps(result,ensure_ascii=False,indent=2)
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(rendered+"\n",encoding="utf-8")
        print("Wrote",a.output)
    else:
        print(rendered)
    if a.strict and (not result["matches_rock5b"] or
                     platform.machine().lower() not in ("aarch64","arm64")):
        print("BLOCKED: expected Radxa ROCK 5B ARM64; refusing to certify this environment.",
              file=sys.stderr)
        return 2
    return 0

if __name__=="__main__":
    sys.exit(main())
