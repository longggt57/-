const { chromium } = require('playwright');
const DIR = '/home/user/kmong-portfolio/docs/portfolio/00_대표/glow/';
const names = ['glow_00_전체맵', 'glow_01_주문취합', 'glow_02_새주문알림', 'glow_03_문의AI', 'glow_04_매출리포트', 'glow_05_의뢰견적', 'glow_06_CRM동기화'];
const only = process.argv[2];
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 900 }, deviceScaleFactor: 1.5 });
  const errs = []; p.on('pageerror', (e) => errs.push(e.message));
  for (let i = 0; i < names.length; i++) {
    if (only && +only !== i) continue;
    await p.goto(`file://${DIR}glow.html?s=${i}`, { waitUntil: 'networkidle' }); await p.waitForTimeout(500);
    await p.screenshot({ path: `${DIR}${names[i]}.png` });
  }
  console.log('errors', errs); await b.close();
})();
