#!/usr/bin/env python3
"""Audit 35 lesson files and local links without network access."""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT=Path(__file__).resolve().parents[1]
MD_LINK=re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)")

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths=[]
    def handle_starttag(self,tag,attrs):
        self.paths.extend(v for k,v in attrs if k in ("src","href") and v)

def resolve(source,url):
    url=url.strip()
    if not url or url.startswith(("#","//","mailto:","data:","javascript:")):
        return None
    info=urlsplit(url)
    if info.scheme or info.netloc or not info.path or info.path.startswith("/"):
        return None
    return source.parent/unquote(info.path)

def run():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--verbose",action="store_true")
    flags=a.parse_args()
    text=(ROOT/"courseware/assets/catalog.js").read_text(encoding="utf8").strip()
    catalog=json.loads(text.removeprefix("window.COURSE_CATALOG=").rstrip("; \n"))
    problems=[]
    if len(catalog)!=35:problems.append("Catalog count not 35")
    required=[]
    for item in catalog:
        i=int(item["id"])
        slug=item["slug"]
        required.extend([ROOT/"docs"/(slug+".md"),ROOT/"courseware/lessons"/(slug+".html"),
                         ROOT/"examples"/f"lesson_{i:02d}.py",
                         ROOT/"examples"/("LESSON_27.md" if i==27 else f"notes/lesson_{i:02d}.md")])
    for p in required:
        if not p.is_file():problems.append("Missing lesson asset: "+str(p))
    if (ROOT/"文本").exists():problems.append("Legacy source directory restored: 文本/")
    count=0
    for doc in list(ROOT.rglob("*.md"))+list((ROOT/"courseware").rglob("*.html")):
        if any(x in (".venv","build","results","downloads") for x in doc.parts):
            continue
        content=doc.read_text(encoding="utf8")
        if doc.suffix==".md":
            content=re.sub(r"(?ms)^\x60{3}.*?^\x60{3}\s*$","",content)
            refs=[m.group(1).split(' "')[0] for m in MD_LINK.finditer(content)]
        else:
            parser=Links();parser.feed(content);refs=parser.paths
        for item in refs:
            target=resolve(doc,item)
            if target is None:continue
            count+=1
            if not target.exists():
                problems.append(f"Broken link {doc.relative_to(ROOT)} -> {item}")
    print(f"Lessons={len(catalog)}, assets={len(required)}, internal_links={count}, errors={len(problems)}")
    for error in problems[:65]:print(error)
    if flags.verbose and not problems:print("All selected local references exist.")
    return int(bool(problems))

if __name__=="__main__":
    raise SystemExit(run())
