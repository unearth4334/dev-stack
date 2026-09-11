#!/usr/bin/env python3
"""Check local documentation links, HTML anchors and illustrative JSON syntax.

No network requests: external URLs are verified during publication/review.
"""
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            if attrs["id"] in self.ids:
                self.errors.append(f'duplicate id: {attrs["id"]}')
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            if attrs.get(key):
                self.links.append(attrs[key])


def main():
    paths = [ROOT / "README.md", ROOT / "CONTRIBUTING.md"]
    paths += sorted((ROOT / "docs").rglob("*.md"))
    paths += sorted((ROOT / "docs").rglob("*.html"))
    pages = {}
    links = []
    errors = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".html":
            page = Page()
            page.feed(text)
            pages[path] = page
            errors.extend(f"{path.relative_to(ROOT)}: {e}" for e in page.errors)
            links.extend((path, link) for link in page.links)
        else:
            links.extend((path, link) for link in re.findall(r"\]\(([^)]+)\)", text))
            defined = set(re.findall(r"^\[\^([^]]+)\]:", text, re.M))
            used = set(re.findall(r"\[\^([^]]+)\](?!:)", text))
            errors.extend(f"{path.relative_to(ROOT)}: undefined footnote {ref}" for ref in used - defined)
    for path, link in links:
        url = urlsplit(link)
        if url.scheme or url.netloc:
            continue
        target = (path.parent / unquote(url.path)).resolve() if url.path else path
        if target.is_dir():
            target /= "index.html"
        if ROOT not in target.parents or not target.is_file():
            errors.append(f"{path.relative_to(ROOT)}: missing local target {link}")
        elif url.fragment and target.suffix == ".html":
            if target not in pages:
                page = Page()
                page.feed(target.read_text(encoding="utf-8"))
                pages[target] = page
            if unquote(url.fragment) not in pages[target].ids:
                errors.append(f"{path.relative_to(ROOT)}: missing HTML anchor {link}")
    for path in (ROOT / "examples").glob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"PASS: {len(paths)} documents; local links, HTML anchors, footnotes and example JSON.")


if __name__ == "__main__":
    main()
