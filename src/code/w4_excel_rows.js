// 택배사 업로드 양식에 맞춰 엑셀 행 만들기
// 열 구성은 '설정' 노드의 columnMap 에서 바꿉니다. 한 줄에 하나씩:
//   엑셀열이름=필드이름        예) 받는분성명=수령인
//   엑셀열이름="고정값"        예) 운임구분="선불"
// 쓸 수 있는 필드: 수령인, 연락처, 주소, 품목, 수량, 배송메모, 주문번호, 상품주문번호, 주문자, 결제금액, 합포장
const cfg = $('설정').first().json;
const { shipments } = $input.first().json;

const columns = String(cfg.columnMap || '')
  .split('\n')
  .map((l) => l.trim())
  .filter((l) => l && !l.startsWith('#') && l.includes('='))
  .map((l) => {
    const i = l.indexOf('=');
    const header = l.slice(0, i).trim();
    const src = l.slice(i + 1).trim();
    const fixed = src.match(/^"(.*)"$/);
    return { header, get: fixed ? () => fixed[1] : (s) => s[src] ?? '' };
  });
if (!columns.length) throw new Error('설정 노드의 columnMap 이 비어 있습니다.');

return shipments.map((s) => {
  const row = {};
  for (const c of columns) row[c.header] = c.get(s);
  return { json: row };
});
