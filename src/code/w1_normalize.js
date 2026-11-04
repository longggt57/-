// 상세 조회 응답 → 구글시트 한 줄 형식으로 정리 + 이미 기록한 주문은 제외
// (활성화된 워크플로에서는 처리한 상품주문번호를 기억해 중복 기록을 막습니다)
const store = $getWorkflowStaticData('global');
store.seen = store.seen || [];
// 데모 모드에서는 매번 같은 샘플을 보여주기 위해 중복 제외를 하지 않습니다
const demo = $('설정').first().json.demoMode === true;
const seen = new Set(demo ? [] : store.seen);

const fmt = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  if (isNaN(d)) return String(iso);
  const k = new Date(d.getTime() + 9 * 3600e3).toISOString();
  return `${k.slice(0, 10)} ${k.slice(11, 19)}`;
};
const collectedAt = fmt(new Date().toISOString());

const rows = [];
for (const item of $input.all()) {
  const list = Array.isArray(item.json.data) ? item.json.data : [item.json];
  for (const d of list) {
    const o = d.order || {};
    const p = d.productOrder || {};
    const s = p.shippingAddress || {};
    const id = String(p.productOrderId || '');
    if (!id || seen.has(id)) continue;
    seen.add(id);
    rows.push({
      결제일시: fmt(o.paymentDate),
      주문일시: fmt(o.orderDate),
      주문번호: String(o.orderId || ''),
      상품주문번호: id,
      상품명: p.productName || '',
      옵션: p.productOption || '',
      수량: Number(p.quantity || 0),
      결제금액: Number(p.totalPaymentAmount || 0),
      주문자: o.ordererName || '',
      수령인: s.name || '',
      연락처: s.tel1 || o.ordererTel || '',
      주소: [s.baseAddress, s.detailedAddress].filter(Boolean).join(' '),
      배송메모: p.shippingMemo || '',
      수집일시: collectedAt,
    });
  }
}

if (!demo) store.seen = [...seen].slice(-5000);
return rows.map((json) => ({ json }));
