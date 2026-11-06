const { chromium } = require('playwright');
const OUT = process.argv[2];
const wfs = [['goQoaeuDCBol9V1Y', 'n8n_00_전체맵'], ['ooBkkjo1wYvU12lJ', 'n8n_01_주문_알림'], ['CpDHjDtWZ1koAV9v', 'n8n_02_AI_리포트'], ['ijSceOleEJzLylKg', 'n8n_03_견적_CRM']];
(async () => {
  const b = await chromium.launch();
  const page = await b.newPage({ viewport: { width: 1600, height: 1200 }, deviceScaleFactor: 1.125, locale: 'ko-KR' });
  await page.goto('http://127.0.0.1:5678/signin', { waitUntil: 'networkidle' }); await page.waitForTimeout(4000);
  await page.locator('input').first().fill('demo@example.com');
  await page.fill('input[name=password]', 'DemoPass123!');
  await page.keyboard.press('Enter'); await page.waitForTimeout(3000);
  for (const [id, n] of wfs) {
    await page.goto(`http://127.0.0.1:5678/workflow/${id}`, { waitUntil: 'networkidle' }); await page.waitForTimeout(3000);
    for (let i = 0; i < 3; i++) { await page.keyboard.press('Escape'); await page.waitForTimeout(200); }
    await page.mouse.click(800, 600); await page.keyboard.press('1'); await page.waitForTimeout(1500);
    await page.mouse.move(1590, 1190); await page.waitForTimeout(400);
    const hid = await page.evaluate(() => { const els = [...document.querySelectorAll('[data-test-id*="issue" i], [class*="issues" i], [data-test-id="node-issues"]')]; els.forEach((e) => (e.style.visibility = 'hidden')); document.querySelectorAll('button').forEach((b) => { if (/^\s*Execute workflow\s*$/i.test(b.textContent) && !b.closest('[class*="footer" i]')) { const r = b.getBoundingClientRect(); if (r.top > 120 && r.top < 1150 && r.height < 30) b.style.visibility = 'hidden'; } }); return els.length; });
    console.log('hidden issue icons', hid);
    await page.screenshot({ path: `${OUT}/${n}.png` });
    console.log('shot', n, page.url());
  }
  await b.close();
})();
