// Claude 응답 해석 → 문의 정보와 합치기
// 응답이 거절(refusal)·잘림(max_tokens)·형식 오류이면 '사람 확인 필요'로 안전하게 넘깁니다.
const res = $input.first().json;
const { inquiry } = $('문의 정리 + AI 요청 구성').first().json;

let ai;
let error = '';
try {
  if (res.stop_reason === 'refusal') throw new Error('AI가 답변을 거절했습니다');
  if (res.stop_reason === 'max_tokens') throw new Error('AI 응답이 길이 제한으로 잘렸습니다');
  const text = (res.content || []).filter((b) => b.type === 'text').map((b) => b.text).join('');
  ai = JSON.parse(text);
} catch (e) {
  error = e.message;
  ai = {
    category: '기타', urgency: '높음', sentiment: '중립',
    summary: inquiry.message.slice(0, 60),
    needs_human: true, human_reason: `AI 처리 실패: ${error}`, draft_reply: '',
  };
}

const urgent = ai.needs_human === true || ai.urgency === '높음';
return [{
  json: {
    ...inquiry,
    ...ai,
    urgent,
    aiModel: res.model || '',
    aiError: error,
    tokens: (res.usage?.input_tokens || 0) + (res.usage?.output_tokens || 0),
  },
}];
