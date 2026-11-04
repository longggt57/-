// 조회 구간 나누기: 네이버 '변경 주문 조회'는 한 번에 최대 24시간만 조회됩니다.
// 평일은 최근 26시간, 월요일은 주말 포함 74시간을 24시간씩 나눠 조회합니다. (겹치는 주문은 '주문 취합'에서 제거)
const cfg = $('설정').first().json;
const token = $input.first().json.access_token;
if (!token) throw new Error('네이버 토큰 발급 실패: 애플리케이션 ID/시크릿을 확인하세요.');

const now = Date.now();
const kstDay = new Date(now + 9 * 3600e3).getUTCDay();
const hours = Number(cfg.naverLookbackHours) > 0 ? Number(cfg.naverLookbackHours) : (kstDay === 1 ? 74 : 26);
const iso = (ms) => new Date(ms + 9 * 3600e3).toISOString().replace('Z', '+09:00');

const out = [];
for (let end = now; end > now - hours * 3600e3; end -= 24 * 3600e3) {
  const start = Math.max(end - 24 * 3600e3, now - hours * 3600e3);
  out.push({ json: { lastChangedFrom: iso(start), lastChangedTo: iso(end), access_token: token } });
}
return out;
