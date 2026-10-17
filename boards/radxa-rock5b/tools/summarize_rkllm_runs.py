#!/usr/bin/env python3
"""Validate and summarize repeated rkllm_stream C API reports (offline only)."""
import argparse
import json
import math
from pathlib import Path
import statistics
import sys

REQUIRED = ("initialized_ms", "run_wall_ms", "text_chunks", "output_utf8_bytes")
OPTIONAL = ("first_text_chunk_ms", "sdk_generate_tokens", "sdk_generate_time_ms",
            "sdk_tokens_per_sec", "sdk_prefill_time_ms", "sdk_peak_memory_mb")
INTEGER = ("text_chunks", "output_utf8_bytes", "sdk_generate_tokens", "max_new_tokens", "context_tokens", "model_size_bytes")
CONFIG = ("max_new_tokens", "context_tokens", "model_size_bytes")

def positive(value, name, allow_zero=False, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    if integer and not isinstance(value, int):
        raise ValueError(f"{name} must be integer")
    if value < 0 if allow_zero else value <= 0:
        raise ValueError(f"{name} must be {'nonnegative' if allow_zero else 'positive'}")
    return value

def load(path):
    def unique(pairs):
        obj = {}
        for k, v in pairs:
            if k in obj:
                raise ValueError(f"duplicate key {k} in {path}")
            obj[k] = v
        return obj
    def nonfinite(v):
        raise ValueError(f"invalid JSON constant {v}")
    report = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique,
                        parse_constant=nonfinite)
    if not isinstance(report, dict) or report.get("backend") != "RKLLM C API":
        raise ValueError(f"{path}: not an RKLLM C API report")
    if report.get("run_status") != 0 or type(report.get("run_status")) is not int:
        raise ValueError(f"{path}: unsuccessful run")
    if report.get("finished_callback") is not True or report.get("callback_error") is not False:
        raise ValueError(f"{path}: incomplete or failed callback")
    if not isinstance(report.get("model_file"), str) or not report["model_file"]:
        raise ValueError(f"{path}: missing model file metadata")
    for key in CONFIG:
        if key in report:
            positive(report[key], key, integer=True)
    for key in REQUIRED:
        positive(report.get(key), key, allow_zero=key in ("initialized_ms", "text_chunks", "output_utf8_bytes"),
                 integer=key in INTEGER)
    if report["text_chunks"] == 0 or report["output_utf8_bytes"] == 0:
        raise ValueError(f"{path}: no generated text")
    for key in OPTIONAL:
        if report.get(key) is not None:
            positive(report[key], key, integer=key in INTEGER)
    tokens = report.get("sdk_generate_tokens")
    duration = report.get("sdk_generate_time_ms")
    rate = report.get("sdk_tokens_per_sec")
    if rate is not None and (tokens is None or duration is None):
        raise ValueError(f"{path}: token rate without token/time source")
    if tokens is not None and duration is not None:
        if rate is None or not math.isclose(rate, tokens * 1000 / duration, rel_tol=.002, abs_tol=.02):
            raise ValueError(f"{path}: inconsistent SDK token rate")
    elif rate is not None:
        raise ValueError(f"{path}: rate requires both SDK measurements")
    return report

def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]

def stats(values):
    if not values:
        return None
    return {"samples": len(values), "mean": round(statistics.mean(values), 3),
            "p50": round(statistics.median(values), 3),
            "p95": round(percentile(values, .95), 3),
            "max": round(max(values), 3)}

def summarize(paths, require_sdk_tokens=False, allow_text=False):
    if not paths:
        raise ValueError("at least one report is required")
    reports = [load(Path(path)) for path in paths]
    if not allow_text and any("generated_text" in r for r in reports):
        raise ValueError("report includes generated_text; remove text before privacy-safe aggregation")
    if require_sdk_tokens and any(r.get("sdk_tokens_per_sec") is None for r in reports):
        raise ValueError("SDK token telemetry missing in at least one report")
    model_paths = {r["model_file"] for r in reports}
    if len(model_paths) != 1:
        raise ValueError("different model_file paths; compare only identical model/config")
    for key in CONFIG:
        values = [r.get(key) for r in reports]
        if len({str(v) for v in values}) != 1:
            raise ValueError(f"inconsistent {key} across runs")
    columns = ("initialized_ms", "run_wall_ms", "first_text_chunk_ms",
               "sdk_generate_tokens", "sdk_generate_time_ms",
               "sdk_tokens_per_sec", "sdk_prefill_time_ms", "sdk_peak_memory_mb")
    return {"runs": len(reports), "configuration": {k: reports[0].get(k) for k in CONFIG}, "sdk_token_runs": sum(r.get("sdk_tokens_per_sec") is not None for r in reports),
            "statistics": {key: stats([r[key] for r in reports if r.get(key) is not None]) for key in columns},
            "hardware_verified": False,
            "note": ("Statistical validation does not prove hardware provenance; first_text_chunk_ms "
                     "is not guaranteed TTFT; text_chunks are not tokens. "
                     "SDK metrics are summarized only where provided.")}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("reports", nargs="+", type=Path)
    p.add_argument("--require-sdk-tokens", action="store_true")
    p.add_argument("--allow-text", action="store_true",
                   help="accept reports containing generated text, but do not include text in summary")
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    try:
        result = summarize(a.reports, a.require_sdk_tokens, a.allow_text)
        data = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if a.output:
            a.output.parent.mkdir(parents=True, exist_ok=True)
            a.output.write_text(data, encoding="utf-8")
        print(data, end="")
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print("INVALID RKLLM REPORT:", exc, file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
