// 엑셀 파일용 행 (구글시트 '택배업로드' 탭과 같은 내용)
const s = $('주문 취합').first().json;
return s.uploadRows.map((r) => ({ json: Object.fromEntries(s.uploadHeaders.map((h, i) => [h, r[i]])) }));
