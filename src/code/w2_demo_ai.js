// [데모 모드] Claude API 응답과 같은 형태의 가짜 응답 (API 키 없이 흐름 시연용)
// 문의 내용의 키워드로 간단히 분류합니다. 실제 운영에서는 '설정'의 demoMode를 false로 바꾸세요.
const { inquiry } = $input.first().json;
const m = inquiry.message;
const has = (...ks) => ks.some((k) => m.includes(k));

let r;
if (has('환불', '파손', '최악', '신고', '불량', '화가')) {
  r = { category: '불만/클레임', urgency: '높음', sentiment: '부정', needs_human: true,
        human_reason: '환불·파손 관련 불만으로 담당자 확인이 필요합니다.',
        draft_reply: `${inquiry.name}님, 불편을 드려 정말 죄송합니다. 말씀하신 상품 상태를 확인할 수 있도록 사진을 보내주시면 담당자가 바로 확인하겠습니다. 확인 후 교환 또는 환불 절차를 안내드리겠습니다. 다시 한번 사과드립니다.` };
} else if (has('배송', '언제', '도착', '송장')) {
  r = { category: '배송', urgency: '보통', sentiment: '중립', needs_human: false, human_reason: '',
        draft_reply: `안녕하세요 ${inquiry.name}님, 문의 주셔서 감사합니다. 평일 오후 2시 이전 결제 건은 당일 출고되며, 출고 후 보통 1~2일 내 도착합니다. 주문번호를 확인해 정확한 배송 상황을 안내드리겠습니다. 감사합니다.` };
} else if (has('교환', '반품', '사이즈')) {
  r = { category: '교환/반품', urgency: '보통', sentiment: '중립', needs_human: false, human_reason: '',
        draft_reply: `안녕하세요 ${inquiry.name}님. 상품 수령 후 7일 이내에는 교환·반품이 가능합니다. 단순 변심의 경우 왕복 배송비 6,000원이 부과됩니다. 마이페이지에서 신청해 주시면 회수 기사님이 방문합니다. 감사합니다.` };
} else {
  r = { category: '상품문의', urgency: '낮음', sentiment: '중립', needs_human: false, human_reason: '',
        draft_reply: `안녕하세요 ${inquiry.name}님, 문의 감사합니다. 말씀하신 내용 확인 후 정확히 안내드리겠습니다. 조금만 기다려 주세요. 감사합니다.` };
}
r.summary = `[데모] ${m.slice(0, 40)}${m.length > 40 ? '…' : ''}`;

return [{
  json: {
    type: 'message', role: 'assistant', model: 'demo', stop_reason: 'end_turn',
    content: [{ type: 'text', text: JSON.stringify(r) }],
    usage: { input_tokens: 0, output_tokens: 0 },
  },
}];
