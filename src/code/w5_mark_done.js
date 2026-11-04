// 알림 발송까지 끝난 뒤에만 '처리 완료'로 기록 (중간에 실패하면 다음 실행 때 다시 포함)
const cfg = $('설정').first().json;
const s = $('주문 취합').first().json;
if (cfg.demoMode !== true) {
  const store = $getWorkflowStaticData('global');
  store.sentIds = [...new Set([...(store.sentIds || []), ...s.processedIds])].slice(-10000);
  store.lastRunAt = s.runAt;
}
return [{ json: { done: true, date: s.date, shipments: s.shipmentCount, issues: s.issueCount } }];
