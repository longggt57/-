// 메일 제목·본문 작성 (파일 있음 / 출고 대상 없음 공통)
const cfg = $('설정').first().json;
const s = $('출고 대상 선별').first().json;
const esc = (t) => String(t ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const has = s.shipmentCount > 0;

const issueRows = s.issues.map((r) => `
  <tr>
    <td style="padding:6px 8px;border-bottom:1px solid #eee">${esc(r.주문번호)}</td>
    <td style="padding:6px 8px;border-bottom:1px solid #eee">${esc(r.수령인)}</td>
    <td style="padding:6px 8px;border-bottom:1px solid #eee">${esc(r.상품명)}</td>
    <td style="padding:6px 8px;border-bottom:1px solid #eee;color:#cf222e">${esc(r.문제)}</td>
  </tr>`).join('');

const html = `
<div style="font-family:-apple-system,'Apple SD Gothic Neo','Malgun Gothic',sans-serif;max-width:600px;color:#1f2328">
  <p style="margin:0;color:#57606a">${esc(cfg.shopName)} · ${s.date} 출고 준비</p>
  <h2 style="margin:4px 0 12px">${has ? `택배 ${s.shipmentCount}건 업로드 파일이 준비됐습니다` : '오늘 출고할 주문이 없습니다'}</h2>
  <table style="border-collapse:collapse;margin-bottom:16px">
    <tr><td style="padding:4px 16px 4px 0;color:#57606a">조회 기간</td><td>${esc(s.window)}</td></tr>
    <tr><td style="padding:4px 16px 4px 0;color:#57606a">주문</td><td>${s.orderCount}건</td></tr>
    <tr><td style="padding:4px 16px 4px 0;color:#57606a">택배</td><td><b>${s.shipmentCount}건</b>${s.combinedCount ? ` (합포장 ${s.combinedCount}건 포함)` : ''}</td></tr>
    <tr><td style="padding:4px 16px 4px 0;color:#57606a">확인 필요</td><td style="color:${s.issues.length ? '#cf222e' : 'inherit'}"><b>${s.issues.length}건</b></td></tr>
  </table>
  ${has ? `<p>첨부한 <b>${esc(s.fileName)}</b> 파일을 택배사 사이트에 업로드하세요.</p>` : ''}
  ${s.issues.length ? `
  <h3 style="margin:20px 0 8px;color:#cf222e">⚠ 확인 필요 (엑셀에 넣지 않았습니다)</h3>
  <table style="width:100%;border-collapse:collapse;font-size:14px">
    <tr style="background:#f6f8fa"><th style="padding:6px 8px;text-align:left">주문번호</th><th style="padding:6px 8px;text-align:left">받는 분</th><th style="padding:6px 8px;text-align:left">상품</th><th style="padding:6px 8px;text-align:left">문제</th></tr>
    ${issueRows}
  </table>
  <p style="font-size:14px">판매자센터에서 주문 정보를 확인한 뒤 따로 접수해 주세요.</p>` : ''}
  <p style="margin-top:20px;padding:10px 12px;background:#fff8c5;border-radius:6px;font-size:14px">
    업로드 전, 그사이 <b>취소·환불된 주문</b>이 없는지 판매자센터에서 한 번 확인해 주세요.
  </p>
  <p style="color:#8c959f;font-size:12px;margin-top:24px">이 메일은 n8n 자동화로 출고일 아침마다 발송됩니다.</p>
</div>`;

return [{
  json: {
    subject: has
      ? `[${cfg.shopName}] ${s.date} 택배 ${s.shipmentCount}건 업로드 파일${s.issues.length ? ` · 확인 필요 ${s.issues.length}건` : ''}`
      : `[${cfg.shopName}] ${s.date} 출고 대상 없음${s.issues.length ? ` · 확인 필요 ${s.issues.length}건` : ''}`,
    html,
  },
  binary: $input.first().binary, // 엑셀 첨부 파일 그대로 전달
}];
