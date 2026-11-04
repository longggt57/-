// 메일 발송이 끝난 뒤에만 '처리 완료'로 기록 (발송 실패 시 다음 실행 때 다시 포함됨)
const cfg = $('설정').first().json;
const s = $('출고 대상 선별').first().json;
if (cfg.demoMode !== true) {
  const store = $getWorkflowStaticData('global');
  store.lastRunAt = s.runAt;
  store.sentIds = [...new Set([...(store.sentIds || []), ...s.processedIds])].slice(-5000);
}
return [{ json: { done: true, date: s.date, shipments: s.shipmentCount, issues: s.issues.length } }];
