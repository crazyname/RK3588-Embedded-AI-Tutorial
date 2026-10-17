#!/usr/bin/env python3
"""Compare two ROCK 5B C++ YOLOv8 JSONL runs with explicit provenance.

This is an offline comparison, NOT proof that either log came from real hardware.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

from validate_cpp_yolo_stream import assess

REQUIRED = ("board", "os_image", "kernel", "npu_driver", "rknn_runtime",
            "rga_version", "model_sha256", "model_contract", "camera_format",
            "camera_width", "camera_height", "camera_fps", "pipeline",
            "measurement_protocol")
SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
NUMERIC = ("camera_width", "camera_height", "camera_fps")
# Changes to any of these invalidate a controlled, single-variable comparison.
COMPARABLE = REQUIRED

def load_manifest(path):
    def no_duplicates(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError(f"duplicate manifest field: {key}")
            obj[key] = value
        return obj
    def bad_constant(value):
        raise ValueError(f"nonfinite JSON constant: {value}")
    doc = json.loads(path.read_text(encoding="utf-8"),
                     object_pairs_hook=no_duplicates, parse_constant=bad_constant)
    if not isinstance(doc, dict):
        raise ValueError("manifest must be a JSON object")
    for field in REQUIRED:
        value = doc.get(field)
        if field in NUMERIC:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"invalid {field}")
            if field in ("camera_width", "camera_height") and (not isinstance(value, int)):
                raise ValueError(f"{field} must be an integer")
        elif not isinstance(value, str) or not value.strip() or value.strip().lower() in ("unknown", "todo", "n/a", "placeholder"):
            raise ValueError(f"missing or placeholder {field}")
    if not SHA256.fullmatch(doc["model_sha256"]):
        raise ValueError("model_sha256 must have 64 hexadecimal characters")
    if "evidence_type" not in doc or doc["evidence_type"] not in ("board-captured", "synthetic"):
        raise ValueError("evidence_type must be board-captured or synthetic")
    if "log_sha256" not in doc or not isinstance(doc["log_sha256"], str) or not SHA256.fullmatch(doc["log_sha256"]):
        raise ValueError("log_sha256 required to bind manifest to log file")
    return doc

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def compare(base_log, base_meta, candidate_log, candidate_meta, allow_mismatch=False):
    a, b = load_manifest(base_meta), load_manifest(candidate_meta)
    if sha256(base_log).lower() != a["log_sha256"].lower():
        raise ValueError("baseline log SHA256 mismatch")
    if sha256(candidate_log).lower() != b["log_sha256"].lower():
        raise ValueError("candidate log SHA256 mismatch")
    first = assess(base_log, a["camera_width"], a["camera_height"])
    second = assess(candidate_log, b["camera_width"], b["camera_height"])
    differences = {field: {"baseline": a[field], "candidate": b[field]}
                   for field in COMPARABLE if a[field] != b[field]}
    # JSONL timing definitions must be identical even when the SDK versions differ.
    if differences and not allow_mismatch:
        raise ValueError("incomparable acquisition configurations: " + ", ".join(differences))
    key = "inference_and_decode_ms"
    old = first["timing"][key]["p95_ms"]
    new = second["timing"][key]["p95_ms"]
    def relative(v1, v2):
        return round((v2 - v1) / v1 * 100, 3) if v1 != 0 else None
    return {
        "comparison_valid": not differences,
        "config_differences": differences,
        "baseline": {"manifest": str(base_meta), "frames": first["frames"], "timing": first["timing"]},
        "candidate": {"manifest": str(candidate_meta), "frames": second["frames"], "timing": second["timing"]},
        "inference_decode_p95_delta_ms": round(new - old, 3),
        "inference_decode_p95_delta_percent": relative(old, new),
        "hardware_verified": False,
        "interpretation": ("Lower p95 means lower recorded inference+decode latency; "
                           "this metric is not standalone NPU compute latency. "
                           "Both log provenance and real board execution require independent evidence.")
    }

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline-jsonl", type=Path, required=True)
    p.add_argument("--baseline-manifest", type=Path, required=True)
    p.add_argument("--candidate-jsonl", type=Path, required=True)
    p.add_argument("--candidate-manifest", type=Path, required=True)
    p.add_argument("--allow-mismatch", action="store_true",
                   help="diagnostics only: results will be marked non-comparable")
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    try:
        result = compare(args.baseline_jsonl, args.baseline_manifest,
                         args.candidate_jsonl, args.candidate_manifest, args.allow_mismatch)
        serialized = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(serialized, encoding="utf-8")
        print(serialized, end="")
        return 0 if result["comparison_valid"] else 3
    except (ValueError, OSError, TypeError, json.JSONDecodeError) as exc:
        print("INVALID BENCHMARK COMPARISON:", exc, file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
