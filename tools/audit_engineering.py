#!/usr/bin/env python3
"""Enforce engineering source -> experiment -> test -> acceptance mapping.

Structural coverage does NOT imply all tests assert behavior or hardware was exercised.
"""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "engineering/manifest.json"
REQUIRED_SECTIONS = ("## 源码清单", "## 实验命令", "## 自动化测试", "## 验收标准", "## 验证边界")
# Handwritten onboard apps, C++ targets and diagnostic tools that require an
# explicit mapping; generated files, headers, mocks and tests are intentionally excluded.
SOURCE_ROOTS = (
    "boards/radxa-rock5b/apps",
    "boards/radxa-rock5b/tools",
    "examples/hardware",
)
EXCLUDE = {"examples/hardware/rkllm/tests/mock_rkllm_runtime.cpp"}
SUPPORTED = {".py", ".cpp"}

def audit(root=ROOT, manifest_path=None):
    path = manifest_path or (root / "engineering/manifest.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    failures = []
    if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("projects"), list):
        raise ValueError("invalid engineering manifest schema")
    covered = set()
    ids = set()
    for project in data["projects"]:
        if not isinstance(project, dict):
            failures.append("project entry not an object")
            continue
        pid = project.get("id")
        if not isinstance(pid, str) or not re.fullmatch(r"[a-z][a-z0-9-]+", pid) or pid in ids:
            failures.append(f"invalid/duplicate ID: {pid}")
            continue
        ids.add(pid)
        runbook = project.get("experiment")
        sources = project.get("sources")
        tests = project.get("tests")
        if not isinstance(runbook, str) or runbook != f"engineering/{pid}.md":
            failures.append(f"{pid}: invalid runbook path")
            continue
        if not isinstance(sources, list) or not sources or not isinstance(tests, list) or not tests:
            failures.append(f"{pid}: empty sources or tests")
            continue
        doc = root / runbook
        if not doc.is_file():
            failures.append(f"{pid}: missing runbook")
        else:
            body = doc.read_text(encoding="utf-8")
            for heading in REQUIRED_SECTIONS:
                if heading not in body:
                    failures.append(f"{pid}: missing {heading}")
            for field, needle in (("acceptance_heading", "## 验收标准"),
                                  ("test_heading", "## 自动化测试"),
                                  ("hardware_heading", "## 验证边界")):
                if project.get(field) != needle:
                    failures.append(f"{pid}: bad {field}")
        for kind, paths in (("source", sources), ("test", tests)):
            for entry in paths:
                if not isinstance(entry, str) or entry.startswith("/") or ".." in Path(entry).parts:
                    failures.append(f"{pid}: unsafe {kind} path")
                    continue
                target = root / entry
                if not target.is_file():
                    failures.append(f"{pid}: missing {kind} {entry}")
                if kind == "source":
                    covered.add(entry)
                if doc.is_file() and f"../{entry}" not in body:
                    failures.append(f"{pid}: {kind} not linked in runbook: {entry}")
    expected = set()
    for part in SOURCE_ROOTS:
        folder = root / part
        if folder.exists():
            for file in folder.rglob("*"):
                if file.suffix not in SUPPORTED or "tests" in file.parts:
                    continue
                rel = file.relative_to(root).as_posix()
                if rel not in EXCLUDE:
                    expected.add(rel)
    missing = sorted(expected - covered)
    failures.extend(f"unmapped engineering source: {source}" for source in missing)
    return len(ids), len(covered), len(expected), failures

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    try:
        count, mapped, sources, failures = audit()
    except (ValueError, OSError, json.JSONDecodeError) as err:
        print("INVALID ENGINEERING MANIFEST:", err, file=sys.stderr)
        return 2
    print(f"projects={count}, mapped_sources={mapped}, discovered_sources={sources}, problems={len(failures)}")
    for problem in failures:
        print(" -", problem)
    return int(bool(failures)) if args.strict else 0

if __name__ == "__main__":
    raise SystemExit(main())
