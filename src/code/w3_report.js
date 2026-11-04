// 슬랙 메시지 + HTML 메일 본문 작성
const cfg = $('설정').first().json;
const s = $input.first().json;
const won = (n) => `${Math.round(Number(n)).toLocaleString('ko-KR')}원`;
const delta = (p) => (p === null || p === undefined ? '비교 데이터 없음' : `${p > 0 ? '▲' : p < 0 ? '▼' : ''}${Math.abs(p)}%`);

// AI 코멘트가 없으면 규칙 기반 기본 코멘트
const fallback = s.orders === 0
  ? '어제는 결제된 주문이 없었습니다. 판매처 연동 상태를 한번 확인해 보세요.'
  : `어제 매출은 지난주 같은 요일 대비 ${delta(s.vsLastWeekPct)}, 최근 7일 평균 대비 ${delta(s.vsAvg7Pct)}입니다.` +
    (s.top[0] ? ` 가장 많이 팔린 상품은 '${s.top[0].name}'입니다.` : '');
const comment = s.comment || fallback;

const max = Math.max(...s.trend.map((t) => t.revenue), 1);
const bars = s.trend.map((t) => {
  const n = Math.round((t.revenue / max) * 12);
  return `${t.date.slice(5)} ${'█'.repeat(n)}${'░'.repeat(12 - n)} ${won(t.revenue)}`;
});

const slackText = [
  `📊 *${cfg.shopName} 일일 매출 리포트* · ${s.date} (${s.weekday})`,
  `*매출 ${won(s.revenue)}* · 주문 ${s.orders}건 · 객단가 ${won(s.avgOrderValue)}`,
  `지난주 ${s.weekday}요일 대비 ${delta(s.vsLastWeekPct)} · 7일 평균 대비 ${delta(s.vsAvg7Pct)}`,
  '',
  `💡 ${comment}`,
  '',
  '*인기 상품 TOP5*',
  ...(s.top.length ? s.top.map((p, i) => `${i + 1}. ${p.name} — ${p.qty}개 / ${won(p.revenue)}`) : ['(없음)']),
  '',
  '*최근 8일 추이*',
  '```' + bars.join('\n') + '```',
].join('\n');

const esc = (t) => String(t).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const color = (p) => (p > 0 ? '#1a7f37' : p < 0 ? '#cf222e' : '#57606a');
const html = `
<div style="font-family:-apple-system,'Apple SD Gothic Neo','Malgun Gothic',sans-serif;max-width:560px;margin:0 auto;color:#1f2328">
  <p style="color:#57606a;margin:0">${esc(cfg.shopName)} · ${s.date} (${s.weekday})</p>
  <h1 style="font-size:28px;margin:4px 0 0">${won(s.revenue)}</h1>
  <p style="margin:4px 0 16px">주문 ${s.orders}건 · 객단가 ${won(s.avgOrderValue)}</p>
  <table style="width:100%;border-collapse:collapse;margin-bottom:16px">
    <tr><td style="padding:8px;background:#f6f8fa">지난주 ${s.weekday}요일 대비</td>
        <td style="padding:8px;background:#f6f8fa;text-align:right;color:${color(s.vsLastWeekPct)}"><b>${delta(s.vsLastWeekPct)}</b> (${won(s.lastWeekRevenue)})</td></tr>
    <tr><td style="padding:8px">최근 7일 평균 대비</td>
        <td style="padding:8px;text-align:right;color:${color(s.vsAvg7Pct)}"><b>${delta(s.vsAvg7Pct)}</b> (${won(s.avg7Revenue)})</td></tr>
  </table>
  <div style="padding:12px 16px;background:#ddf4ff;border-radius:8px;margin-bottom:16px">💡 ${esc(comment)}</div>
  <h3 style="margin:0 0 8px">인기 상품 TOP5</h3>
  <table style="width:100%;border-collapse:collapse">
    ${s.top.map((p, i) => `<tr><td style="padding:6px 0;border-bottom:1px solid #d0d7de">${i + 1}. ${esc(p.name)}</td><td style="padding:6px 0;border-bottom:1px solid #d0d7de;text-align:right">${p.qty}개 · ${won(p.revenue)}</td></tr>`).join('')}
  </table>
  <p style="color:#8c959f;font-size:12px;margin-top:24px">이 메일은 n8n 자동화로 매일 아침 발송됩니다.</p>
</div>`;

return [{
  json: {
    ...s,
    comment,
    slackText,
    emailSubject: `[${cfg.shopName}] ${s.date} 매출 ${won(s.revenue)} (${delta(s.vsLastWeekPct)})`,
    emailHtml: html,
  },
}];
