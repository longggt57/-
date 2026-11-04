// 문의 기록용 시트 한 줄
const d = $input.first().json;
return [{
  json: {
    접수일시: d.receivedAt,
    채널: d.channel,
    고객명: d.name,
    이메일: d.email,
    주문번호: d.orderNo,
    분류: d.category,
    긴급도: d.urgency,
    감정: d.sentiment,
    요약: d.summary,
    사람확인: d.urgent ? 'Y' : 'N',
    확인사유: d.human_reason,
    문의내용: d.message,
    답변초안: d.draft_reply,
    처리상태: '대기',
  },
}];
