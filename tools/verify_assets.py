#!/usr/bin/env python3
"""Check local model files and optional SHA256 values. Never downloads any files."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda:file.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def assess(entry,root):
    expected=entry.get("sha256")
    if expected is not None and not re.fullmatch("[0-9a-fA-F]{64}",expected):
        raise ValueError("Invalid SHA256 for model "+entry["id"])
    path=entry.get("local_path")
    if path is None:
        return {"id":entry["id"],"state":"manual-resource-required"}
    name=Path(path)
    if name.is_absolute() or ".." in name.parts:
        raise ValueError("Asset local_path must remain inside the repository")
    candidate=root/name
    if not candidate.is_file():
        return {"id":entry["id"],"state":"missing","path":path}
    actual=digest(candidate)
    result={"id":entry["id"],"state":"ok","bytes":candidate.stat().st_size,
            "sha256":actual,"trusted_hash_verified":False}
    if expected:
        if actual.lower()!=expected.lower():
            result["state"]="hash-mismatch"
        else:
            result["trusted_hash_verified"]=True
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest",type=Path,default=ROOT/"models/manifest.json")
    p.add_argument("--id",help="model id from the manifest")
    p.add_argument("--list",action="store_true")
    p.add_argument("--strict",action="store_true")
    args=p.parse_args()
    manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("schema_version")!=1:
        p.error("unsupported resource manifest schema")
    entries=manifest["models"]
    if len(set(x["id"] for x in entries))!=len(entries):
        p.error("duplicate model id")
    if args.id:
        entries=[x for x in entries if x["id"]==args.id]
        if not entries:p.error("unknown model id")
    failures=0
    for entry in entries:
        if args.list:
            print(entry["id"],entry["source_url"])
            continue
        value=assess(entry,ROOT)
        print(json.dumps(value,ensure_ascii=False))
        if value["state"]=="hash-mismatch" or args.strict and value["state"]!="ok":
            failures+=1
    return 1 if failures else 0

if __name__=="__main__":
    raise SystemExit(main())
