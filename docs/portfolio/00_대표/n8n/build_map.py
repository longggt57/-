#!/usr/bin/env python3
"""n8n 화면 캡처용 '자동화 시스템 맵' 워크플로 JSON을 만듭니다 (실행용이 아니라 구조를 보여주는 용도).
python3 docs/portfolio/00_대표/n8n/build_map.py → 같은 폴더에 map_all.json, map_1.json~map_3.json"""
import json, uuid
from pathlib import Path
D = Path(__file__).resolve().parent
T = {  # 노드 종류: (type, typeVersion, 기본 파라미터)
 'sched': ('n8n-nodes-base.scheduleTrigger', 1.2, {'rule': {'interval': [{'field': 'hours'}]}}),
 'hook': ('n8n-nodes-base.webhook', 2, {'path': 'inquiry', 'httpMethod': 'POST'}),
 'form': ('n8n-nodes-base.formTrigger', 2.2, {'formTitle': '의뢰서'}),
 'http': ('n8n-nodes-base.httpRequest', 4.2, {'url': 'https://api.example.com'}),
 'code': ('n8n-nodes-base.code', 2, {'jsCode': 'return $input.all();'}),
 'merge': ('n8n-nodes-base.merge', 3, {}),
 'merge3': ('n8n-nodes-base.merge', 3, {'numberInputs': 3}),
 'if': ('n8n-nodes-base.if', 2.2, {}),
 'set': ('n8n-nodes-base.set', 3.4, {}),
 'file': ('n8n-nodes-base.convertToFile', 1.1, {'operation': 'xlsx'}),
 'sheet': ('n8n-nodes-base.googleSheets', 4.5, {}),
 'gmail': ('n8n-nodes-base.gmail', 2.1, {}),
 'slack': ('n8n-nodes-base.slack', 2.3, {}),
 'notion': ('n8n-nodes-base.notion', 2.2, {}),
 'claude': ('@n8n/n8n-nodes-langchain.anthropic', 1, {'resource': 'text', 'operation': 'message'}),
}
# 레인: 제목, 설명, 색, 노드[(key, 이름, 종류, col, row)], 연결[(from, to, out, in)]
LANES = [
 ('① 주문 취합 → 택배 엑셀 · 구글 시트', '스마트스토어·쿠팡 주문을 매일 아침 모아 합포장하고, 택배 업로드 엑셀과 날짜별 구글 시트를 만들어 메일로 보냅니다', 4,
  [('t', '매일 08:40', 'sched', 0, 0), ('a', '스마트스토어 주문 조회', 'http', 1, -1), ('b', '쿠팡 주문 조회', 'http', 1, 1), ('m', '주문 합치기', 'merge', 2, 0),
   ('c', '합포장 · 주소 정리', 'code', 3, 0), ('x', '택배 업로드 엑셀', 'file', 4, 0), ('s', '구글 시트 생성', 'sheet', 5, 0), ('g', '담당자 메일', 'gmail', 6, 0)],
  [('t', 'a'), ('t', 'b'), ('a', 'm', 0, 0), ('b', 'm', 0, 1), ('m', 'c'), ('c', 'x'), ('x', 's'), ('s', 'g')]),
 ('② 새 주문 알림', '10분마다 새 주문을 확인해 시트에 기록하고 슬랙으로 알립니다', 5,
  [('t', '10분마다', 'sched', 0, 0), ('a', '신규 주문 조회', 'http', 1, 0), ('i', '새 주문 있음?', 'if', 2, 0), ('s', '주문 시트 기록', 'sheet', 3, -1), ('k', '슬랙 알림', 'slack', 4, -1)],
  [('t', 'a'), ('a', 'i'), ('i', 's', 0, 0), ('s', 'k')]),
 ('③ 고객 문의 AI 답변 초안', '문의가 들어오면 Claude가 분류하고 답변 초안을 쓰며, 급한 문의는 담당자를 바로 호출합니다', 6,
  [('t', '문의 접수', 'hook', 0, 0), ('a', '문의 내용 정리', 'set', 1, 0), ('c', 'Claude 분류 · 답변 초안', 'claude', 2, 0), ('i', '긴급 문의?', 'if', 3.5, 0),
   ('k', '담당자 슬랙 호출', 'slack', 4.7, -1), ('s', '답변 초안 저장', 'sheet', 4.7, 1)],
  [('t', 'a'), ('a', 'c'), ('c', 'i'), ('i', 'k', 0, 0), ('i', 's', 1, 0)]),
 ('④ 일일 매출 리포트', '매일 아침 어제 주문을 집계해 채널별 매출 리포트를 메일로 보냅니다', 3,
  [('t', '매일 08:30', 'sched', 0, 0), ('a', '어제 주문 읽기', 'sheet', 1, 0), ('c', '매출 집계', 'code', 2, 0), ('h', '리포트 작성', 'code', 3, 0), ('g', '리포트 메일', 'gmail', 4, 0)],
  [('t', 'a'), ('a', 'c'), ('c', 'h'), ('h', 'g')]),
 ('⑤ 의뢰 분석 → 견적 · 계약 DB', '의뢰서를 Claude가 분석해 견적을 계산하고, 계약 DB에 등록한 뒤 회신 초안을 만듭니다', 2,
  [('t', '의뢰서 접수', 'form', 0, 0), ('c', 'Claude 의뢰 분석', 'claude', 1, 0), ('p', '견적 계산', 'code', 2.5, 0), ('n', '계약 DB 등록', 'notion', 3.5, 0), ('g', '회신 초안 메일', 'gmail', 4.5, 0)],
  [('t', 'c'), ('c', 'p'), ('p', 'n'), ('n', 'g')]),
 ('⑥ 통합 CRM · 정기배송 동기화', '카페24·스마트스토어·공구·전화주문을 매시간 모아 고객과 정기배송을 맞추고 CRM 대시보드를 갱신합니다', 7,
  [('t', '매시간', 'sched', 0, 0), ('a', '카페24 주문', 'http', 1, -1), ('b', '스마트스토어 주문', 'http', 1, 0), ('d', '공구 · 전화주문 시트', 'sheet', 1, 1),
   ('m', '채널 통합', 'merge3', 2, 0), ('c', '고객 · 정기배송 매칭', 'code', 3, 0), ('u', 'CRM DB 업데이트', 'http', 4, 0), ('k', '이상 건 알림', 'slack', 5, 0)],
  [('t', 'a'), ('t', 'b'), ('t', 'd'), ('a', 'm', 0, 0), ('b', 'm', 0, 1), ('d', 'm', 0, 2), ('m', 'c'), ('c', 'u'), ('u', 'k')]),
]
URLS = {'스마트스토어 주문 조회': 'https://api.commerce.naver.com/external/v1/pay-order/seller/product-orders/last-changed-statuses',
        '쿠팡 주문 조회': 'https://api-gateway.coupang.com/v2/providers/openapi/apis/api/v4/vendors/ordersheets',
        '신규 주문 조회': 'https://api.commerce.naver.com/external/v1/pay-order/seller/product-orders/last-changed-statuses',
        '카페24 주문': 'https://mall.cafe24api.com/api/v2/admin/orders',
        '스마트스토어 주문': 'https://api.commerce.naver.com/external/v1/pay-order/seller/product-orders/query',
        'CRM DB 업데이트': 'https://crm.mall.co.kr/api/sync'}
DX, DY, LANE_W, LANE_H = 240, 165, 1720, 540
def build(name, idx, cols):
    nodes, conns = [], {}
    for n, li in enumerate(idx):
        title, desc, color, ns, cs = LANES[li]
        ox, oy = (n % cols) * (LANE_W + 80), (n // cols) * (LANE_H + 60)
        nodes.append({'parameters': {'content': f'## {title}\n{desc}', 'height': LANE_H, 'width': LANE_W, 'color': color}, 'type': 'n8n-nodes-base.stickyNote', 'typeVersion': 1,
                      'position': [ox, oy], 'id': str(uuid.uuid4()), 'name': f'메모 {li + 1}'})
        names = {}
        for key, label, kind, col, row in ns:
            ty, ver, p = T[kind]
            if kind == 'http': p = {'url': URLS.get(label, 'https://api.example.com'), **({'method': 'POST'} if 'CRM' in label else {})}
            names[key] = label if label not in [x['name'] for x in nodes] else f'{label} ({li + 1})'
            nodes.append({'parameters': p, 'type': ty, 'typeVersion': ver, 'position': [round(ox + 80 + col * DX), round(oy + 250 + row * DY)], 'id': str(uuid.uuid4()), 'name': names[key]})
        for c in cs:
            f, t = c[0], c[1]; o = c[2] if len(c) > 2 else 0; i = c[3] if len(c) > 3 else 0
            main = conns.setdefault(names[f], {'main': []})['main']
            while len(main) <= o: main.append([])
            main[o].append({'node': names[t], 'type': 'main', 'index': i})
    wf = {'name': name, 'nodes': nodes, 'connections': conns, 'settings': {'executionOrder': 'v1'}, 'pinData': {}, 'active': False}
    return wf
out = {'map_all': build('자동화 시스템 전체 맵', range(6), 2), 'map_1': build('주문 · 알림 자동화', [0, 1], 1),
       'map_2': build('AI · 리포트 자동화', [2, 3], 1), 'map_3': build('견적 · CRM 자동화', [4, 5], 1)}
for k, wf in out.items(): (D / f'{k}.json').write_text(json.dumps(wf, ensure_ascii=False, indent=1), encoding='utf-8')
print('✓', ', '.join(out))
