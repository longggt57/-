// 주문 취합: 판매처별 주문 합치기 → 이미 처리한 주문 제외 → 검증 → 합포장 → 시트·엑셀용 표 만들기
const cfg = $('설정').first().json;
const demo = cfg.demoMode === true;
const store = $getWorkflowStaticData('global');

// 1) 실행된 판매처 노드에서 주문 모으기
const SOURCES = ['샘플 주문 (데모)', '스마트스토어 정리', '쿠팡 정리'];
const all = [];
const notes = [];
for (const name of SOURCES) {
  let node;
  try { node = $(name); } catch { continue; }
  if (!node.isExecuted) continue;
  for (const it of node.all()) {
    all.push(...(it.json.orders || []));
    if (it.json.note) notes.push(`${it.json.channel}: ${it.json.note}`);
  }
}

// 2) 이미 처리한 주문 제외 (활성화된 워크플로에서만 기억)
const done = new Set(demo ? [] : store.sentIds || []);
const seen = new Set();
const fresh = all.filter((o) => {
  const id = `${o.판매처}:${o.상품주문번호}`;
  if (!o.상품주문번호 || done.has(id) || seen.has(id)) return false;
  seen.add(id);
  return true;
}).sort((a, b) => String(a.결제일시).localeCompare(String(b.결제일시)));

// 3) 검증
const phoneOk = (p) => /^0\d{1,3}-?\d{3,4}-?\d{4}$/.test(String(p || '').replace(/\s/g, '')); // 쿠팡 안심번호 0503 포함
const ok = [], issues = [];
for (const o of fresh) {
  const p = [];
  if (!String(o.수령인 || '').trim()) p.push('받는 분 없음');
  if (!phoneOk(o.연락처)) p.push('연락처 형식 오류');
  if (String(o.주소 || '').trim().length < 8) p.push('주소 없음/불완전');
  (p.length ? issues : ok).push(p.length ? { ...o, 문제: p.join(', ') } : o);
}

// 4) 합포장: 받는 분 + 주소가 같으면 판매처가 달라도 한 박스 (쿠팡은 안심번호라 연락처는 비교하지 않음)
const item = (o) => `${o.상품명}${o.옵션 ? `(${o.옵션})` : ''} x${Number(o.수량) || 1}`;
const groups = new Map();
for (const o of ok) {
  const key = cfg.combineSameAddress
    ? [o.수령인, String(o.주소).replace(/\s/g, '')].join('|')
    : `${o.판매처}:${o.상품주문번호}`;
  if (!groups.has(key)) groups.set(key, []);
  groups.get(key).push(o);
}
const shipments = [...groups.values()].map((g) => ({
  판매처: [...new Set(g.map((o) => o.판매처))].join('+'),
  수령인: g[0].수령인,
  연락처: (g.find((o) => o.판매처 !== '쿠팡') || g[0]).연락처, // 실번호가 있으면 우선
  우편번호: g.find((o) => o.우편번호)?.우편번호 || '',
  주소: g[0].주소,
  품목: g.map(item).join(' / '),
  수량: g.reduce((s, o) => s + (Number(o.수량) || 1), 0),
  배송메모: [...new Set(g.map((o) => o.배송메모).filter(Boolean))].join(' / '),
  주문번호: [...new Set(g.map((o) => o.주문번호))].join(','),
  상품주문번호: g.map((o) => o.상품주문번호).join(','),
  결제금액: g.reduce((s, o) => s + (Number(o.결제금액) || 0), 0),
  합포장: g.length > 1 ? `${g.length}건 합침` : '',
}));

// 5) 택배 업로드 열 구성 (설정 → columnMap)
const cols = String(cfg.columnMap || '').split('\n').map((l) => l.trim())
  .filter((l) => l && !l.startsWith('#') && l.includes('='))
  .map((l) => { const i = l.indexOf('='); const src = l.slice(i + 1).trim(); const fx = src.match(/^"(.*)"$/);
    return { h: l.slice(0, i).trim(), get: fx ? () => fx[1] : (s) => s[src] ?? '' }; });
if (!cols.length) throw new Error('설정 노드의 columnMap 이 비어 있습니다.');

const ORDER_COLS = ['판매처', '결제일시', '주문번호', '상품주문번호', '상품명', '옵션', '수량', '결제금액', '주문자', '수령인', '연락처', '우편번호', '주소', '배송메모'];
const ISSUE_COLS = ['판매처', '주문번호', '수령인', '연락처', '주소', '상품명', '문제'];
const table = (headers, rows, get = (r, h) => r[h]) => [headers, ...rows.map((r) => headers.map((h) => get(r, h) ?? ''))];

const kstNow = new Date(Date.now() + 9 * 3600e3);
const date = kstNow.toISOString().slice(0, 10);
const time = kstNow.toISOString().slice(11, 16);
const byChannel = {};
for (const o of fresh) byChannel[o.판매처] = (byChannel[o.판매처] || 0) + 1;

const title = `${date} 출고 · 택배 ${shipments.length}건${demo ? ' (데모)' : ''}`;
const TABS = ['택배업로드', '주문전체', '확인필요'];

return [{
  json: {
    date, time, title,
    fileName: `${date}_택배업로드.xlsx`,
    orderCount: fresh.length,
    shipmentCount: shipments.length,
    combinedCount: shipments.filter((s) => s.합포장).length,
    issueCount: issues.length,
    byChannel,
    notes,
    issues,
    uploadHeaders: cols.map((c) => c.h),
    uploadRows: shipments.map((s) => cols.map((c) => c.get(s))),
    sheets: {
      택배업로드: [cols.map((c) => c.h), ...shipments.map((s) => cols.map((c) => c.get(s)))],
      주문전체: table(ORDER_COLS, fresh),
      확인필요: table(ISSUE_COLS, issues),
    },
    // 구글 스프레드시트 새 파일 만들기 요청 (Sheets API)
    createRequest: {
      properties: { title: `[${cfg.shopName}] ${title}`, locale: 'ko_KR', timeZone: 'Asia/Seoul' },
      sheets: TABS.map((t, i) => ({ properties: { sheetId: i, title: t, index: i, gridProperties: { frozenRowCount: 1 } } })),
    },
    processedIds: fresh.map((o) => `${o.판매처}:${o.상품주문번호}`),
    runAt: Date.now(),
  },
}];
