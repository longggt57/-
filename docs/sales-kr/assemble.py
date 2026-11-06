#!/usr/bin/env python3
"""sales.html = 머리말 + style.css + body.html. 고친 뒤 실행: python3 docs/sales-kr/assemble.py"""
from pathlib import Path
D = Path(__file__).resolve().parent
head = '''<title>브랜드랩 매출관리</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gothic+A1:wght@400;500;600;700;800&family=Roboto+Mono:wght@500&display=swap">
<style>
'''
(D / 'sales.html').write_text(head + (D / 'style.css').read_text(encoding='utf-8') + '</style>\n\n' + (D / 'body.html').read_text(encoding='utf-8'), encoding='utf-8')
print('✓ docs/sales-kr/sales.html')
