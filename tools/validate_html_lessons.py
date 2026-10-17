#!/usr/bin/env python3
"""Validate 35 continuously scrolling HTML lessons and their embedded JSON.

Static check only: JavaScript/browser rendering still requires separate visual QA.
"""
from html.parser import HTMLParser
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CATALOG=ROOT/"courseware/assets/catalog.js"

class LessonPage(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.payloads={}
        self.current=None
        self.scripts=[]
        self.styles=[]
        self.app_count=0
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=="script":
            if attrs.get("src"):self.scripts.append(attrs["src"])
            if attrs.get("id") in ("lesson-data","lesson-depth"):
                self.current=attrs["id"]
                self.payloads[self.current]=[]
        elif tag=="link" and attrs.get("rel")=="stylesheet":
            self.styles.append(attrs.get("href"))
        elif tag=="div" and attrs.get("id")=="app":
            self.app_count+=1
    def handle_data(self,data):
        if self.current is not None:self.payloads[self.current].append(data)
    def handle_endtag(self,tag):
        if tag=="script":self.current=None

def audit():
    text=CATALOG.read_text(encoding="utf8").strip()
    prefix="window.COURSE_CATALOG="
    if not text.startswith(prefix):
        raise ValueError("Bad course catalog syntax")
    catalog=json.loads(text[len(prefix):].rstrip("; \n"))
    errors=[]
    for item in catalog:
        n=int(item["id"])
        path=ROOT/"courseware/lessons"/(item["slug"]+".html")
        if not path.is_file():
            errors.append(f"{n:02d}: missing HTML {path.name}")
            continue
        page=LessonPage()
        page.feed(path.read_text(encoding="utf8"))
        if page.app_count!=1:
            errors.append(f"{n:02d}: expected one continuous content root, got {page.app_count}")
        for asset in ("../assets/catalog.js","../assets/extras.js","../assets/player.js"):
            if asset not in page.scripts:
                errors.append(f"{n:02d}: missing lesson JS {asset}")
        if "../assets/style.css" not in page.styles:
            errors.append(f"{n:02d}: missing lesson stylesheet")
        values={}
        for name in ("lesson-data","lesson-depth"):
            if name not in page.payloads:
                errors.append(f"{n:02d}: missing {name}")
                continue
            try:
                values[name]=json.loads("".join(page.payloads[name]))
            except json.JSONDecodeError as exc:
                errors.append(f"{n:02d}: invalid {name} JSON: {exc}")
        if len(values)!=2:continue
        data,depth=values["lesson-data"],values["lesson-depth"]
        if data.get("id")!=n:errors.append(f"{n:02d}: lesson id mismatch")
        if not isinstance(data.get("title"),str) or not data["title"]:
            errors.append(f"{n:02d}: missing title")
        for key in ("goals","steps","checks"):
            if not isinstance(data.get(key),list) or not data[key]:
                errors.append(f"{n:02d}: missing core teaching content {key}")
        for key,minimum in (("concepts",3),("lab",3),("diagnosis",2),("refs",2)):
            if not isinstance(depth.get(key),list) or len(depth[key])<minimum:
                errors.append(f"{n:02d}: depth {key} must contain >= {minimum} items")
        if not isinstance(depth.get("case"),dict):
            errors.append(f"{n:02d}: missing applied case")

        # Required teaching walkthroughs: P0 toolkit/inference/metrics and core deployment lessons.
        # This protects teaching alignment without adding hardware mocks or regression machinery.
        if n in (5, 8, 9, 13, 14, 15, 16) or 24 <= n <= 34:
            walk=depth.get("walkthrough")
            md_path=ROOT/"docs"/(item["slug"]+".md")
            if not isinstance(walk,dict) or len(walk.get("steps",[]))<3:
                errors.append(f"{n:02d}: missing substantive API walkthrough")
            elif not md_path.is_file():
                errors.append(f"{n:02d}: missing matching Markdown walkthrough")
            else:
                markdown=md_path.read_text(encoding="utf8")
                if "## 源码精读：关键 API、张量与验收" not in markdown:
                    errors.append(f"{n:02d}: Markdown code walkthrough heading missing")
                for step in walk["steps"]:
                    api=step.get("api","")
                    if not api or api not in markdown:
                        errors.append(f"{n:02d}: API explanation not synced: {api}")
    if len(catalog)!=35:
        errors.append(f"Expected 35 lessons, found {len(catalog)}")
    print(f"HTML lessons checked={len(catalog)}, problems={len(errors)}")
    for error in errors[:60]:print(error)
    return int(bool(errors))

if __name__=="__main__":
    raise SystemExit(audit())
