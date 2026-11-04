// 변경된 주문 목록에서 결제완료(PAYED) 상품주문번호 추출
// 새 주문이 없어도 빈 목록 1건을 내보내서 다음 판매처(쿠팡) 조회가 이어지게 합니다.
// 조회 구간이 여러 개면 응답도 여러 개 → 모두 합칩니다
const list = $input.all().flatMap((i) => i.json?.data?.lastChangeStatuses ?? []);
const ids = [...new Set(list
  .filter((s) => !s.lastChangedType || s.lastChangedType === 'PAYED')
  .map((s) => String(s.productOrderId)))];
if (!ids.length) return [{ json: { productOrderIds: [] } }];
const chunks = [];
for (let i = 0; i < ids.length; i += 300) chunks.push({ json: { productOrderIds: ids.slice(i, i + 300) } });
return chunks; // 상세 조회 API는 한 번에 최대 300건
// 참고: 한 구간 변경 건이 아주 많으면 응답에 다음 페이지(more)가 생깁니다. 하루 수천 건 규모면 페이지 처리를 추가하세요.
