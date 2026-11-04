// Claude 응답에서 코멘트 추출 (실패하면 빈 값 → 기본 코멘트 사용)
const res = $input.first().json;
const stats = $('AI 요청 구성').first().json;
const ok = res.stop_reason === 'end_turn';
const comment = ok
  ? (res.content || []).filter((b) => b.type === 'text').map((b) => b.text).join('').trim()
  : '';
const { request, ...rest } = stats;
return [{ json: { ...rest, comment } }];
