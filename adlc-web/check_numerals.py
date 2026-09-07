#!/usr/bin/env python3
"""Guard: no Western digits in Arabic page content.

The kit's bilingual rule is "never mix numeral systems in one view", so any
number this generator prints on an Arabic page must be Arabic-Indic. Content
that is deliberately in another language — a staff composer's English field, a
member's verbatim message — is marked `data-foreign` and skipped, which is also
why those elements carry lang/dir.
"""
import sys, re
from html.parser import HTMLParser
from pathlib import Path

VOID = {"area","base","br","col","embed","hr","img","input","link","meta","source","track","wbr"}
SKIP_TAGS = {"script","style"}
ALLOW = ("AED", "W53", "FBMA", "EN", "adlc.ae")

class Extract(HTMLParser):
    def __init__(self, root_classes):
        super().__init__(convert_charrefs=True)
        self.root_classes, self.depth, self.inside = root_classes, 0, 0
        self.skip_until, self.stack, self.out = None, [], []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in VOID: return
        self.stack.append(tag)
        d = len(self.stack)
        if self.skip_until is None and (tag in SKIP_TAGS or "data-foreign" in a):
            self.skip_until = d
        if self.inside == 0 and any(c in (a.get("class") or "").split() for c in self.root_classes):
            self.inside = d
    def handle_endtag(self, tag):
        if tag in VOID or not self.stack: return
        d = len(self.stack)
        if self.skip_until == d: self.skip_until = None
        if self.inside == d: self.inside = 0
        self.stack.pop()
    def handle_data(self, data):
        if self.inside and self.skip_until is None:
            self.out.append(data)

def main(dist="dist"):
    bad = []
    for f in sorted(Path(dist, "ar").glob("*.html")):
        p = Extract({"page-head", "app-body", "cs-body"})
        # <main> has no class; give it one to hook onto
        p.feed(f.read_text(encoding="utf-8").replace("<main ", '<main class="app-body" ')
                                            .replace("<main>", '<main class="app-body">'))
        text = "".join(p.out)
        for token in ALLOW: text = text.replace(token, "")
        hits = sorted(set(re.findall(r"[0-9]+", text)))
        if hits: bad.append((f.name, hits[:5]))
    if bad:
        print("FAIL — Western digits on Arabic pages:")
        for n, h in bad: print("   ", n, h)
        return 1
    print("OK  no Western digits on Arabic pages (%d scanned)" % len(list(Path(dist,"ar").glob("*.html"))))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "dist"))
