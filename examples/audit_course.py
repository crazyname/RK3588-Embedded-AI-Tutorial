#!/usr/bin/env python3
"""Read-only structural audit of all 35 lesson scripts, docs and practical runbooks.

A dedicated script is not automatically a complete model deployment or NPU verification.
"""
import argparse
import ast
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent.parent

def audit():
    raw=(ROOT/"courseware/assets/catalog.js").read_text(encoding="utf-8").strip()
    prefix="window.COURSE_CATALOG="
    if not raw.startswith(prefix):
        raise ValueError("Unknown catalog format")
    catalog=json.loads(raw[len(prefix):].rstrip("; \n"))
    if len(catalog)!=35:
        raise ValueError("Catalog should contain 35 lessons")
    rows=[]
    for item in catalog:
        n=int(item["id"]);slug=item["slug"]
        code=ROOT/"examples"/f"lesson_{n:02d}.py"
        content=code.read_text(encoding="utf-8") if code.is_file() else ""
        try:
            if content:ast.parse(content,filename=str(code))
            valid=bool(content)
        except SyntaxError:
            valid=False
        stub=bool(re.search(r"(?m)^from\s+labs\s+import\s+main\s*$",content)
             and re.search(r"\bmain\(\s*\d+\s*\)",content))
        note=ROOT/"examples/notes"/f"lesson_{n:02d}.md"
        if n==27 and not note.is_file():
            note=ROOT/"examples/LESSON_27.md"
        rows.append({
          "lesson":n,
          "source":str(code.relative_to(ROOT)),
          "implementation":"thin_wrapper" if stub else "dedicated_script" if content else "missing",
          "python_syntax_ok":valid,
          "markdown_exists":(ROOT/"docs"/f"{slug}.md").is_file(),
          "html_exists":(ROOT/"courseware/lessons"/f"{slug}.html").is_file(),
          "runbook_exists":note.is_file()
        })
    return {"total":len(rows),
            "dedicated":sum(x["implementation"]=="dedicated_script" for x in rows),
            "thin":sum(x["implementation"]=="thin_wrapper" for x in rows),
            "missing_runbooks":sum(not x["runbook_exists"] for x in rows),
            "invalid":sum(not all(x[k] for k in ("python_syntax_ok","markdown_exists","html_exists")) for x in rows),
            "hardware_verified":"NOT CHECKED (requires real RK3588)",
            "entries":rows}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json",action="store_true",help="emit machine-readable JSON")
    ap.add_argument("--strict",action="store_true",
                    help="after all lessons complete: fail on any thin scripts or missing runbook")
    a=ap.parse_args()
    result=audit()
    if a.json:
        print(json.dumps(result,ensure_ascii=False,indent=2))
    else:
        print(f"{result['dedicated']}/{result['total']} dedicated sources; "
              f"{result['thin']} thin wrappers; {result['missing_runbooks']} missing runbooks.")
        for row in result["entries"]:
            print(f"{row['lesson']:02d} {row['implementation']:16s} "
                  f"syntax={row['python_syntax_ok']} MD={row['markdown_exists']} "
                  f"HTML={row['html_exists']} runbook={row['runbook_exists']}")
        print("This is a source-layout audit, not functional correctness or real board validation.")
    return int(result["invalid"]>0 or
               (a.strict and (result["thin"]>0 or result["missing_runbooks"]>0)))

if __name__=="__main__":
    raise SystemExit(main())
