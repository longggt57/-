// 어제(KST) 매출 집계 + 지난주 같은 요일 / 최근 7일 평균 비교 + 상품 TOP5
const rows = $input.all().map((i) => i.json);

const kstNow = new Date(Date.now() + 9 * 3600e3);
const dayStr = (offset) => new Date(kstNow.getTime() - offset * 86400e3).toISOString().slice(0, 10);
const target = dayStr(1);
const lastWeek = dayStr(8);
const recent7 = Array.from({ length: 7 }, (_, i) => dayStr(i + 2)); // 어제 이전 7일

const byDay = {};
const seen = new Set();
for (const r of rows) {
  const date = String(r.결제일시 || '').slice(0, 10);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) continue;
  const id = String(r.상품주문번호 || '');
  if (id) { if (seen.has(id)) continue; seen.add(id); }
  const amount = Number(String(r.결제금액).replace(/[^0-9.-]/g, '')) || 0;
  const qty = Number(r.수량) || 0;
  const d = (byDay[date] ||= { orders: 0, revenue: 0, items: 0, products: {} });
  d.orders += 1;
  d.revenue += amount;
  d.items += qty;
  const p = (d.products[r.상품명 || '(이름 없음)'] ||= { qty: 0, revenue: 0 });
  p.qty += qty;
  p.revenue += amount;
}

const empty = { orders: 0, revenue: 0, items: 0, products: {} };
const y = byDay[target] || empty;
const lw = byDay[lastWeek] || empty;
const avg7 = recent7.reduce((s, d) => s + (byDay[d]?.revenue || 0), 0) / 7;
const pct = (a, b) => (b ? Math.round(((a - b) / b) * 1000) / 10 : null);

const top = Object.entries(y.products)
  .map(([name, v]) => ({ name, ...v }))
  .sort((a, b) => b.revenue - a.revenue)
  .slice(0, 5);

const trend = [...recent7].reverse().concat(target).map((d) => ({ date: d, revenue: byDay[d]?.revenue || 0 }));

return [{
  json: {
    date: target,
    weekday: '일월화수목금토'[new Date(target + 'T00:00:00Z').getUTCDay()],
    orders: y.orders,
    revenue: y.revenue,
    items: y.items,
    avgOrderValue: y.orders ? Math.round(y.revenue / y.orders) : 0,
    lastWeekRevenue: lw.revenue,
    vsLastWeekPct: pct(y.revenue, lw.revenue),
    avg7Revenue: Math.round(avg7),
    vsAvg7Pct: pct(y.revenue, avg7),
    top,
    trend,
  },
}];
