// [데모 모드] '주문' 시트에서 읽어온 것과 같은 형식의 최근 35일 샘플 데이터
// (워크플로 ①이 기록하는 열 이름과 동일)
const products = [
  ['[1+1] 국산 무농약 현미 4kg', 32900, 9],
  ['제주 감귤 5kg 가정용', 20900, 7],
  ['유기농 귀리 1kg', 12900, 5],
  ['햇 찹쌀 2kg', 15900, 3],
  ['국산 서리태 1kg', 18900, 2],
  ['혼합 잡곡 선물세트', 45000, 1],
];
// 재현 가능한 의사난수 (매번 같은 데모 결과)
let seed = 20261104;
const rnd = () => ((seed = (seed * 1103515245 + 12345) % 2147483648) / 2147483648);

const rows = [];
const now = Date.now() + 9 * 3600e3; // KST 기준
for (let day = 35; day >= 1; day--) {
  const base = new Date(now - day * 86400e3);
  const weekend = [0, 6].includes(base.getUTCDay());
  const n = Math.round((weekend ? 14 : 22) + rnd() * 10 + (35 - day) * 0.3);
  for (let k = 0; k < n; k++) {
    const pick = rnd() * 27;
    let acc = 0;
    const p = products.find(([, , w]) => (acc += w) >= pick) || products[0];
    const qty = rnd() < 0.8 ? 1 : 2;
    const t = new Date(base);
    t.setUTCHours(Math.floor(rnd() * 24), Math.floor(rnd() * 60), 0);
    const iso = t.toISOString();
    rows.push({
      결제일시: `${iso.slice(0, 10)} ${iso.slice(11, 19)}`,
      상품주문번호: `D${iso.slice(0, 10).replace(/-/g, '')}${String(k).padStart(4, '0')}`,
      상품명: p[0],
      수량: qty,
      결제금액: p[1] * qty,
    });
  }
}
return rows.map((json) => ({ json }));
