#!/usr/bin/env python3
"""sales.html (fragment) -> index.html (standalone page for GitHub Pages).

Run after editing sales.html:  python3 docs/sales-en/build_page.py
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
frag = (HERE / "sales.html").read_text(encoding="utf-8")
reset = (":root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}"
         "body{margin:0}img{max-width:100%}[hidden]{display:none!important}")
head, sep, rest = frag.partition("<style>")
html = (
    '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    f"<style>{reset}</style>\n{head}</head>\n<body>\n{sep}{rest}\n</body>\n</html>\n"
)
(HERE / "index.html").write_text(html, encoding="utf-8")
print("✓ docs/sales-en/index.html")
