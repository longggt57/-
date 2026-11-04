// 쿠팡 Wing Open API 요청 준비 (발주서 목록 조회)
// 서명 = HMAC-SHA256( signed-date + method + path + query , Secret Key ) → 다음 '쿠팡 서명' 노드가 계산
// Secret Key 는 이 파일이 아니라 n8n 자격증명(Crypto → Hmac Secret)에 저장합니다.
const cfg = $('설정').first().json;
const vendorId = String(cfg.coupangVendorId || '').trim();
if (!vendorId) throw new Error('설정 노드에 coupangVendorId(업체코드, 예: A00012345)를 입력하세요.');

const kst = (offsetDays) => new Date(Date.now() + 9 * 3600e3 - offsetDays * 86400e3).toISOString().slice(0, 10);
const path = `/v2/providers/openapi/apis/api/v4/vendors/${vendorId}/ordersheets`;
const query = [
  `createdAtFrom=${kst(Number(cfg.coupangLookbackDays || 2))}`,
  `createdAtTo=${kst(0)}`,
  `status=${cfg.coupangStatus || 'ACCEPT'}`,   // ACCEPT=결제완료, INSTRUCT=상품준비중
  'maxPerPage=50',
].join('&');

// signed-date: yyMMdd'T'HHmmss'Z' (UTC)
const signedDate = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '').slice(2);
return [{ json: { path, query, signedDate, message: `${signedDate}GET${path}${query}` } }];
