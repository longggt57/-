// 메일·슬랙 알림 내용 (출고 있음 / 없음 공통)
const cfg = $('설정').first().json;
const s = $('주문 취합').first().json;
let sheetUrl = '';
try { if ($('시트 쓰기 요청 구성').isExecuted) sheetUrl = $('시트 쓰기 요청 구성').first().json.spreadsheetUrl || ''; } catch {}
const esc = (t) => String(t ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const has = s.shipmentCount > 0;
const channels = Object.entries(s.byChannel).map(([k, v]) => `${k} ${v}건`).join(' · ') || '새 주문 없음';

const issueRows = s.issues.map((r) => `<tr><td style="padding:6px 8px;border-bottom:1px solid #eee">${esc(r.판매처)}</td><td style="padding:6px 8px;border-bottom:1px solid #eee">${esc(r.주문번호)}</td><td style="padding:6px 8px;border-bottom:1px solid #eee">${esc(r.수령인)}</td><td style="padding:6px 8px;border-bottom:1px solid #eee;color:#cf222e">${esc(r.문제)}</td></tr>`).join('');

const html = `
<div style="font-family:-apple-system,'Apple SD Gothic Neo','Malgun Gothic',sans-serif;max-width:600px;color:#1f2328">
  <p style="margin:0;color:#57606a">${esc(cfg.shopName)} · ${s.date} ${s.time} 출고 준비</p>
  <h2 style="margin:4px 0 12px">${has ? `택배 ${s.shipmentCount}건 준비됐습니다` : '오늘 출고할 새 주문이 없습니다'}</h2>
  <table style="border-collapse:collapse;margin-bottom:16px">
    <tr><td style="padding:4px 16px 4px 0;color:#57606a">판매처별 주문</td><td>${esc(channels)}</td></tr>
    <tr><td style="padding:4px 16px 4px 0;color:#57606a">택배</td><td><b>${s.shipmentCount}건</b>${s.combinedCount ? ` (합포장 ${s.combinedCount}건)` : ''}</td></tr>
    <tr><td style="padding:4px 16px 4px 0;color:#57606a">확인 필요</td><td style="color:${s.issueCount ? '#cf222e' : 'inherit'}"><b>${s.issueCount}건</b></td></tr>
  </table>
  ${has && sheetUrl ? `<p><a href="${esc(sheetUrl)}" style="display:inline-block;background:#1d4ed8;color:#fff;padding:10px 16px;border-radius:6px;text-decoration:none;font-weight:600">구글 스프레드시트 열기</a></p>` : ''}
  ${has ? `<p>택배사 업로드용 <b>${esc(s.fileName)}</b> 파일을 첨부했습니다.</p>` : ''}
  ${s.issueCount ? `<h3 style="margin:20px 0 8px;color:#cf222e">⚠ 확인 필요 (업로드 파일에 넣지 않았습니다)</h3>
  <table style="width:100%;border-collapse:collapse;font-size:14px"><tr style="background:#f6f8fa"><th style="padding:6px 8px;text-align:left">판매처</th><th style="padding:6px 8px;text-align:left">주문번호</th><th style="padding:6px 8px;text-align:left">받는 분</th><th style="padding:6px 8px;text-align:left">문제</th></tr>${issueRows}</table>` : ''}
  ${s.notes.length ? `<p style="font-size:13px;color:#9a6700">${s.notes.map(esc).join('<br>')}</p>` : ''}
  <p style="margin-top:20px;padding:10px 12px;background:#fff8c5;border-radius:6px;font-size:14px">업로드 전, 그사이 <b>취소·환불된 주문</b>이 없는지 판매자센터에서 확인해 주세요.</p>
  <p style="color:#8c959f;font-size:12px;margin-top:24px">n8n 자동화로 출고일 아침마다 발송됩니다.</p>
</div>`;

const slackText = [
  has ? `📦 *${s.date} 출고 준비 · 택배 ${s.shipmentCount}건*${s.combinedCount ? ` (합포장 ${s.combinedCount})` : ''}` : `📦 *${s.date} 출고할 새 주문 없음*`,
  channels,
  s.issueCount ? `⚠ 확인 필요 ${s.issueCount}건: ${s.issues.map((i) => `${i.수령인 || '?'}(${i.문제})`).join(', ')}` : '',
  sheetUrl ? `<${sheetUrl}|구글 스프레드시트 열기>` : '',
].filter(Boolean).join('\n');

return [{
  json: {
    subject: `[${cfg.shopName}] ${s.date} ${has ? `택배 ${s.shipmentCount}건 업로드 파일` : '출고 대상 없음'}${s.issueCount ? ` · 확인 필요 ${s.issueCount}건` : ''}`,
    html, slackText, sheetUrl,
  },
  binary: $input.first().binary,
}];
