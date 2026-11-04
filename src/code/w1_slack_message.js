// 신규 주문 요약 슬랙 메시지 (개인정보는 마스킹)
const rows = $input.all().map((i) => i.json);
const total = rows.reduce((s, r) => s + Number(r.결제금액 || 0), 0);
const won = (n) => `${Number(n).toLocaleString('ko-KR')}원`;
const mask = (name) => (name ? name[0] + '*'.repeat(Math.max(1, name.length - 1)) : '');

const lines = rows.slice(0, 10).map(
  (r) => `• ${r.상품명} (${r.옵션 || '옵션 없음'}) ×${r.수량} — ${won(r.결제금액)} / ${mask(r.주문자)}`
);
if (rows.length > 10) lines.push(`…외 ${rows.length - 10}건`);

const cfg = $('설정').first().json;
const text = [
  `🛒 *신규 주문 ${rows.length}건* · 합계 ${won(total)}`,
  ...lines,
  cfg.sheetUrl ? `<${cfg.sheetUrl}|주문 시트 열기>` : '',
].filter(Boolean).join('\n');

return [{ json: { text, count: rows.length, total } }];
