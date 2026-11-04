// 변경된 주문 목록에서 '결제완료(PAYED)' 상품주문번호만 추출
// 새 주문이 없으면 빈 배열을 반환 → 이후 노드는 실행되지 않음
const res = $input.first().json;
const list = res?.data?.lastChangeStatuses ?? [];
const ids = [...new Set(
  list
    .filter((s) => !s.lastChangedType || s.lastChangedType === 'PAYED')
    .map((s) => String(s.productOrderId))
)];

if (ids.length === 0) return [];

// 상세 조회 API는 한 번에 최대 300건
const chunks = [];
for (let i = 0; i < ids.length; i += 300) chunks.push(ids.slice(i, i + 300));
return chunks.map((productOrderIds) => ({ json: { productOrderIds } }));
