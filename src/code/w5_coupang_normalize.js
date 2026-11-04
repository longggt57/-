// 쿠팡 발주서 목록 → 공통 주문 형식 (발주서 1건에 상품이 여러 개면 상품마다 한 줄)
const res = $input.first().json;
if (res.code && Number(res.code) !== 200) throw new Error(`쿠팡 API 오류: ${res.message || res.code}`);
const money = (v) => (v && typeof v === 'object' ? Number(v.units ?? v.amount ?? 0) : Number(v || 0));
const fmt = (s) => String(s || '').replace('T', ' ').slice(0, 19);

const orders = [];
for (const sheet of (Array.isArray(res.data) ? res.data : [])) {
  const r = sheet.receiver || {};
  const items = Array.isArray(sheet.orderItems) && sheet.orderItems.length ? sheet.orderItems : [{}];
  for (const it of items) {
    orders.push({
      판매처: '쿠팡',
      주문번호: String(sheet.orderId || ''),
      상품주문번호: `${sheet.shipmentBoxId || ''}-${it.vendorItemId || ''}`,
      결제일시: fmt(sheet.paidAt || sheet.orderedAt),
      상품명: it.sellerProductName || it.vendorItemName || '',
      옵션: it.sellerProductItemName || '',
      수량: Number(it.shippingCount || 1),
      결제금액: money(it.orderPrice),
      주문자: sheet.orderer?.name || '',
      수령인: r.name || '',
      연락처: r.safeNumber || r.receiverNumber || '',
      우편번호: r.postCode || '',
      주소: [r.addr1, r.addr2].filter(Boolean).join(' '),
      배송메모: sheet.parcelPrintMessage || '',
      shipmentBoxId: String(sheet.shipmentBoxId || ''), // 송장 등록 때 필요
    });
  }
}
const note = res.nextToken ? '다음 페이지가 있습니다(50건 초과). 조회 기간을 줄이거나 페이지 처리를 추가하세요.' : '';
return [{ json: { channel: '쿠팡', orders, note } }];
