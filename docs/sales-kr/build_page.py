#!/usr/bin/env python3
"""sales.html(본문 조각) → index.html(GitHub Pages 등에 바로 올리는 완성 페이지).

sales.html 을 고친 뒤 실행하세요:  python3 docs/sales-kr/build_page.py
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
frag = (HERE / "sales.html").read_text(encoding="utf-8")
reset = (":root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}"
         "body{margin:0}img{max-width:100%}[hidden]{display:none!important}")
head, sep, rest = frag.partition("<style>")
html = (
    '<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    f"<style>{reset}</style>\n{head}</head>\n<body>\n{sep}{rest}\n</body>\n</html>\n"
)
(HERE / "index.html").write_text(html, encoding="utf-8")
print("✓ docs/sales-kr/index.html")
