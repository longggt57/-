// 네이버 커머스 API 토큰 발급용 전자서명 생성
// client_secret_sign = base64( bcrypt( client_id + "_" + timestamp, client_secret ) )
// n8n Cloud에서도 동작하도록 bcrypt 구현을 이 노드 안에 내장했습니다(외부 모듈 불필요).

/*__BCRYPT_BUNDLE__*/

const cfg = $('설정').first().json;
const clientId = String(cfg.naverClientId || '').trim();
const clientSecret = String(cfg.naverClientSecret || '').trim();
if (!clientId || !clientSecret) {
  throw new Error('설정 노드에 naverClientId / naverClientSecret 을 입력하세요.');
}

const timestamp = Date.now();
const hashed = bcrypt.hashSync(`${clientId}_${timestamp}`, clientSecret);
const sign = Buffer.from(hashed, 'utf-8').toString('base64');

// 조회 시작 시각: 지금으로부터 lookbackMinutes 전 (KST, ISO 8601)
const lookback = Number(cfg.lookbackMinutes || 15);
const from = new Date(Date.now() - lookback * 60 * 1000);
const kst = new Date(from.getTime() + 9 * 3600 * 1000).toISOString().replace('Z', '+09:00');

return [{
  json: {
    client_id: clientId,
    timestamp: String(timestamp),
    client_secret_sign: sign,
    grant_type: 'client_credentials',
    type: 'SELF',
    lastChangedFrom: kst,
  },
}];
