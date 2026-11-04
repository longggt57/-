// 담당자 슬랙 메시지 작성 (긴급/일반 공통)
const d = $input.first().json;
const head = d.urgent
  ? `🚨 *사람 확인 필요* · ${d.category} · 긴급도 ${d.urgency}`
  : `💬 *새 문의* · ${d.category} · 긴급도 ${d.urgency}`;

const text = [
  head,
  `> ${d.summary}`,
  `고객: ${d.name} · 채널: ${d.channel}${d.orderNo ? ` · 주문번호 ${d.orderNo}` : ''}`,
  d.urgent && d.human_reason ? `사유: ${d.human_reason}` : '',
  '',
  '*원문*',
  '```' + d.message + '```',
  d.draft_reply ? '*AI 답변 초안* (확인 후 복사해서 보내세요)' : '',
  d.draft_reply ? '```' + d.draft_reply + '```' : '',
].filter((l) => l !== '').join('\n');

return [{ json: { ...d, slackText: text } }];
