#!/usr/bin/env python3
"""Bind an RKLLM run report to exact model/prompt bytes without exposing their contents.

Manifest is local evidence, not proof of authentic RK3588 hardware execution.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as inp:
        for block in iter(lambda: inp.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def load_report(path):
    def distinct(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON field: {key}")
            result[key] = value
        return result
    data = json.loads(Path(path).read_text(encoding="utf-8"),
                      object_pairs_hook=distinct,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError("non-finite JSON")))
    if not isinstance(data, dict) or data.get("backend") != "RKLLM C API":
        raise ValueError("expected native RKLLM report")
    if type(data.get("run_status")) is not int or data["run_status"] != 0:
        raise ValueError("RKLLM execution failed")
    if data.get("finished_callback") is not True or data.get("callback_error") is not False:
        raise ValueError("RKLLM callback incomplete")
    for key in ("context_tokens", "max_new_tokens", "model_size_bytes"):
        value = data.get(key)
        if type(value) is not int or value <= 0:
            raise ValueError(f"invalid or missing {key}")
    return data

def create(report_path, model_path, prompt_path):
    report = load_report(report_path)
    if Path(model_path).stat().st_size != report["model_size_bytes"]:
        raise ValueError("model file size differs from native report")
    # Hash the files actually supplied by the operator; a model can change even at the same path.
    return {"format_version": 1, "report_sha256": sha256(report_path),
            "model_sha256": sha256(model_path), "prompt_sha256": sha256(prompt_path),
            "context_tokens": report["context_tokens"],
            "max_new_tokens": report["max_new_tokens"],
            "model_size_bytes": report["model_size_bytes"],
            "hardware_verified": False,
            "note": "Integrity binding only; metadata does not certify genuine board execution."}

def verify(manifest_path, report_path, model_path, prompt_path):
    def duplicates(pairs):
        output = {}
        for k, v in pairs:
            if k in output:
                raise ValueError(f"duplicate manifest field {k}")
            output[k] = v
        return output
    old = json.loads(Path(manifest_path).read_text(encoding="utf-8"),
                     object_pairs_hook=duplicates,
                     parse_constant=lambda x: (_ for _ in ()).throw(ValueError("non-finite JSON")))
    if not isinstance(old, dict) or old.get("format_version") != 1:
        raise ValueError("unsupported manifest format")
    current = create(report_path, model_path, prompt_path)
    for key in current:
        if old.get(key) != current[key]:
            raise ValueError(f"manifest mismatch: {key}")
    return current

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--prompt", required=True, type=Path)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--output", type=Path, help="create a manifest")
    group.add_argument("--verify", type=Path, help="verify an existing manifest")
    args = parser.parse_args()
    try:
        if args.output:
            result = create(args.report, args.model, args.prompt)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        else:
            result = verify(args.verify, args.report, args.model, args.prompt)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print("INVALID RKLLM PROVENANCE:", exc, file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
