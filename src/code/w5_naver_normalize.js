// 스마트스토어 상품주문 상세 → 공통 주문 형식
const fmt = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  if (isNaN(d)) return String(iso);
  const k = new Date(d.getTime() + 9 * 3600e3).toISOString();
  return `${k.slice(0, 10)} ${k.slice(11, 19)}`;
};
const orders = [];
for (const { json } of $input.all()) {
  for (const d of (Array.isArray(json.data) ? json.data : [])) {
    const o = d.order || {};
    const p = d.productOrder || {};
    const s = p.shippingAddress || {};
    orders.push({
      판매처: '스마트스토어',
      주문번호: String(o.orderId || ''),
      상품주문번호: String(p.productOrderId || ''),
      결제일시: fmt(o.paymentDate || o.orderDate),
      상품명: p.productName || '',
      옵션: p.productOption || '',
      수량: Number(p.quantity || 1),
      결제금액: Number(p.totalPaymentAmount || 0),
      주문자: o.ordererName || '',
      수령인: s.name || '',
      연락처: s.tel1 || '',
      우편번호: s.zipCode || '',
      주소: [s.baseAddress, s.detailedAddress].filter(Boolean).join(' '),
      배송메모: p.shippingMemo || '',
    });
  }
}
return [{ json: { channel: '스마트스토어', orders } }];
