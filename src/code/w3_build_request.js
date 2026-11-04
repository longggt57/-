// 집계 결과 → Claude에게 한 줄 코멘트 요청
const cfg = $('설정').first().json;
const s = $input.first().json;

const request = {
  model: cfg.model,
  max_tokens: 4000,
  system: [
    `당신은 온라인 쇼핑몰 "${cfg.shopName}" 사장님의 매출 비서입니다.`,
    '주어진 숫자만 근거로, 사장님이 아침에 읽을 코멘트를 2~3문장으로 씁니다.',
    '- 첫 문장: 어제 실적을 지난주 같은 요일·최근 7일 평균과 비교해 한마디로 평가',
    '- 둘째 문장: 눈에 띄는 상품이나 변화 1가지',
    '- (선택) 셋째 문장: 오늘 해볼 만한 행동 1가지',
    '숫자를 지어내지 말고, 과장하지 말고, 이모지·마크다운 없이 평문으로 쓰세요.',
  ].join('\n'),
  messages: [{ role: 'user', content: `어제 매출 데이터(JSON):\n${JSON.stringify(s)}` }],
  output_config: { effort: 'low' },
  fallbacks: 'default',
};
return [{ json: { ...s, request } }];
