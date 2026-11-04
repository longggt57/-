// 출고 대상 선별
// 1) 지난 실행 이후 결제된 주문만 (처음 실행이면 최근 24시간, 월요일이면 48시간)
// 2) 이미 엑셀로 보낸 상품주문번호는 제외
// 3) 받는 사람·연락처·주소가 이상한 주문은 '확인 필요'로 분리 (엑셀에 넣지 않음)
// 4) 같은 사람·같은 주소 주문은 한 박스로 합치기 (설정: combineSameAddress)
const cfg = $('설정').first().json;
const demo = cfg.demoMode === true;
const store = $getWorkflowStaticData('global');

const KST = 9 * 3600e3;
const nowMs = Date.now();
const kstNow = new Date(nowMs + KST);
const fallbackHours = kstNow.getUTCDay() === 1 ? 48 : 24; // 월요일은 주말 주문 포함
const fromMs = !demo && store.lastRunAt ? store.lastRunAt : nowMs - fallbackHours * 3600e3;

// "YYYY-MM-DD HH:MM:SS"(KST) → ms
const parse = (s) => {
  const m = String(s || '').match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?/);
  return m ? Date.UTC(+m[1], m[2] - 1, +m[3], +m[4], +m[5], +(m[6] || 0)) - KST : NaN;
};
const fmt = (ms) => new Date(ms + KST).toISOString().slice(0, 16).replace('T', ' ');

const sent = new Set(demo ? [] : store.sentIds || []);
const seen = new Set();
const picked = [];
for (const { json: r } of $input.all()) {
  const t = parse(r.결제일시);
  const id = String(r.상품주문번호 || '');
  if (isNaN(t) || t < fromMs || t > nowMs) continue;
  if (id && (sent.has(id) || seen.has(id))) continue;
  if (id) seen.add(id);
  picked.push(r);
}

// 검증
const phoneOk = (p) => /^0\d{1,3}-?\d{3,4}-?\d{4}$/.test(String(p || '').replace(/\s/g, ''));
const ok = [];
const issues = [];
for (const r of picked) {
  const problems = [];
  if (!String(r.수령인 || '').trim()) problems.push('받는 사람 없음');
  if (!phoneOk(r.연락처)) problems.push('연락처 형식 오류');
  if (String(r.주소 || '').trim().length < 8) problems.push('주소 없음/불완전');
  if (problems.length) issues.push({ ...r, 문제: problems.join(', ') });
  else ok.push(r);
}

// 품목 표기: 상품명(옵션) x수량
const item = (r) => `${r.상품명}${r.옵션 ? `(${r.옵션})` : ''} x${Number(r.수량) || 1}`;

let shipments;
if (cfg.combineSameAddress) {
  const groups = new Map();
  for (const r of ok) {
    const key = [r.수령인, String(r.연락처).replace(/\D/g, ''), String(r.주소).replace(/\s/g, '')].join('|');
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(r);
  }
  shipments = [...groups.values()].map((g) => ({
    수령인: g[0].수령인,
    연락처: g[0].연락처,
    주소: g[0].주소,
    품목: g.map(item).join(' / '),
    수량: g.reduce((s, r) => s + (Number(r.수량) || 1), 0),
    배송메모: [...new Set(g.map((r) => r.배송메모).filter(Boolean))].join(' / '),
    주문번호: [...new Set(g.map((r) => r.주문번호))].join(','),
    상품주문번호: g.map((r) => r.상품주문번호).join(','),
    주문자: g[0].주문자,
    결제금액: g.reduce((s, r) => s + (Number(r.결제금액) || 0), 0),
    합포장: g.length > 1 ? `${g.length}건 합침` : '',
  }));
} else {
  shipments = ok.map((r) => ({ ...r, 품목: item(r), 합포장: '' }));
}

const date = kstNow.toISOString().slice(0, 10);
return [{
  json: {
    date,
    fileName: `${date}_택배업로드.xlsx`,
    window: `${fmt(fromMs)} ~ ${fmt(nowMs)}`,
    orderCount: picked.length,
    shipmentCount: shipments.length,
    combinedCount: shipments.filter((s) => s.합포장).length,
    shipments,
    issues,
    processedIds: picked.map((r) => String(r.상품주문번호 || '')).filter(Boolean),
    runAt: nowMs,
  },
}];
