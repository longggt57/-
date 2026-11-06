#!/usr/bin/env python3
"""crm.html = 공통 콘솔 CSS(console-en) + extra.css + body.html. 고친 뒤 실행: python3 docs/crm-en/assemble.py"""
from pathlib import Path
D = Path(__file__).resolve().parent
src = (D.parent / 'console-en' / 'console.html').read_text(encoding='utf-8')
head = src[:src.index('</style>')].replace('<title>Seller Operations Console</title>', '<title>Fernlight Support CRM</title>')
(D / 'crm.html').write_text(head + (D / 'extra.css').read_text(encoding='utf-8') + '</style>\n\n' + (D / 'body.html').read_text(encoding='utf-8'), encoding='utf-8')
print('✓ docs/crm-en/crm.html')
