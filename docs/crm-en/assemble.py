#!/usr/bin/env python3
"""crm.html = 머리말(제목·글꼴) + style.css + body.html. 고친 뒤 실행: python3 docs/crm-en/assemble.py"""
from pathlib import Path
D = Path(__file__).resolve().parent
head = '''<title>Fernlight Support CRM</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700&family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
'''
(D / 'crm.html').write_text(head + (D / 'style.css').read_text(encoding='utf-8') + '</style>\n\n' + (D / 'body.html').read_text(encoding='utf-8'), encoding='utf-8')
print('✓ docs/crm-en/crm.html')
