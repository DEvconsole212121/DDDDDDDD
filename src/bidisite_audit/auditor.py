"""Static checks: not a replacement for WCAG audits or browser-based testing."""
from __future__ import annotations
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from html.parser import HTMLParser

ARABIC = re.compile(r"[\u0621-\u064A\u066E-\u06D3\u06FA-\u06FF]")
VOID = set("area base br col embed hr img input link meta param source track wbr".split())
SKIP = {"script", "style", "template", "svg", "noscript"}

@dataclass(frozen=True)
class Finding:
    file: str
    line: int
    rule: str
    severity: str
    message: str

    def to_dict(self):
        return asdict(self)

class Auditor(HTMLParser):
    def __init__(self, name):
        super().__init__(convert_charrefs=True)
        self.name = name
        self.findings = []
        self.stack = []
        self.ids = set()
        self.labels = set()
        self.controls = []
        self.seen_html = self.viewport = False
        self.title = []
        self.noticed = set()

    def add(self, rule, message, severity="warning", line=None):
        self.findings.append(Finding(self.name, line or self.getpos()[0], rule, severity, message))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        line = self.getpos()[0]
        parent = self.stack[-1] if self.stack else {}
        lang = (attrs.get("lang") or parent.get("lang") or "").lower()
        direction = (attrs.get("dir") or parent.get("dir") or "").lower()
        if tag == "html":
            self.seen_html = True
            if not attrs.get("lang"):
                self.add("html-lang", "Declare the document language.", "error", line)
            if lang.startswith("ar") and direction != "rtl":
                self.add("arabic-document-direction", 'Consider dir="rtl" on Arabic documents.', line=line)
        if "dir" in attrs and attrs["dir"] not in {"ltr", "rtl", "auto"}:
            self.add("invalid-dir", "Direction must be ltr, rtl, or auto.", "error", line)
        if tag == "meta" and (attrs.get("name") or "").lower() == "viewport":
            self.viewport = True
        if tag == "img" and "alt" not in attrs:
            self.add("img-alt", "Provide alt text, or alt=\"\" for decorative images.", "error", line)
        if tag == "input" and attrs.get("type", "").lower() == "image" and not attrs.get("alt"):
            self.add("image-input-alt", "Image submit inputs require alt text.", "error", line)
        if tag == "label" and attrs.get("for"):
            self.labels.add(attrs["for"])
        if tag in {"input", "select", "textarea"} and attrs.get("type", "").lower() not in {"hidden", "button", "submit", "reset", "image"}:
            self.controls.append((line, tag, attrs.get("id", ""), any(f["tag"] == "label" for f in self.stack),
                attrs.get("aria-label", ""), attrs.get("aria-labelledby", ""), attrs.get("title", "")))
        if attrs.get("id"):
            if attrs["id"] in self.ids:
                self.add("duplicate-id", "Element ID is repeated.", "error", line)
            self.ids.add(attrs["id"])
        if tag == "a" and (attrs.get("target") or "").lower() == "_blank" and "noopener" not in (attrs.get("rel") or "").lower().split():
            self.add("external-link-noopener", "Consider rel=noopener on new-tab links.", line=line)
        if tag not in VOID:
            self.stack.append({"tag": tag, "lang": lang, "dir": direction})

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]["tag"] == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        if any(f["tag"] == "title" for f in self.stack):
            self.title.append(data)
        if not ARABIC.search(data) or any(f["tag"] in SKIP for f in self.stack):
            return
        ctx = self.stack[-1] if self.stack else {}
        line = self.getpos()[0]
        if not ctx.get("lang", "").startswith("ar") and (line, "lang") not in self.noticed:
            self.add("arabic-text-lang", 'Consider lang="ar" for Arabic text.', line=line)
            self.noticed.add((line, "lang"))
        if ctx.get("dir") not in {"rtl", "auto"} and (line, "dir") not in self.noticed:
            self.add("arabic-text-direction", 'Consider dir="rtl" or "auto" for Arabic text.', line=line)
            self.noticed.add((line, "dir"))

    def finish(self):
        if not self.seen_html:
            self.add("html-element", "No html element found.", line=1)
        if self.seen_html and not self.viewport:
            self.add("viewport", "Consider a responsive viewport declaration.", line=1)
        if self.seen_html and not "".join(self.title).strip():
            self.add("document-title", "Add a descriptive page title.", line=1)
        for line, tag, id_, wrapped, label, labelledby, title in self.controls:
            has_name = bool(wrapped or label.strip() or title.strip() or (id_ and id_ in self.labels))
            if labelledby and all(ref in self.ids for ref in labelledby.split()):
                has_name = True
            if not has_name:
                self.add("form-control-name", f"<{tag}> needs an accessible name.", "error", line)
        return sorted(self.findings, key=lambda f: (f.line, f.rule))

def audit_html(path, root=None):
    path = Path(path)
    display = str(path.relative_to(root)) if root else str(path)
    parser = Auditor(display)
    try:
        parser.feed(path.read_text(encoding="utf-8-sig"))
        parser.close()
    except (OSError, UnicodeError) as e:
        return [Finding(display, 1, "file-read", "error", str(e))]
    return parser.finish()

def audit_path(target):
    target = Path(target).resolve()
    if not target.exists():
        raise FileNotFoundError(target)
    if target.is_file():
        if target.suffix.lower() not in {".html", ".htm"}:
            raise ValueError("Expected .html or .htm")
        return audit_html(target, target.parent)
    excluded = {".git", ".venv", "venv", "node_modules", "dist", "build"}
    paths = sorted(p for p in target.rglob("*") if p.is_file() and not p.is_symlink() and
                   p.suffix.lower() in {".html", ".htm"} and not set(p.relative_to(target).parts).intersection(excluded))
    if not paths:
        raise ValueError("No HTML files in directory")
    return [finding for path in paths for finding in audit_html(path, target)]
