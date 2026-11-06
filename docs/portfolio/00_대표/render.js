const { chromium } = require('playwright');
const DIR = '/home/user/kmong-portfolio/docs/portfolio/00_대표/';
const names = ['01_표지', '02_시스템맵', '03_구축사례', '04_주문취합', '05_전용웹사이트', '06_가능한자동화', '07_진행방식'];
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1300, height: 1000 }, deviceScaleFactor: 1.5 });
  await p.goto('file://' + DIR + 'slides.html', { waitUntil: 'networkidle' }); await p.waitForTimeout(800);
  for (let i = 0; i < 7; i++) {
    const el = await p.$('#s' + (i + 1));
    const over = await el.evaluate((s) => [...s.querySelectorAll('*')].filter((x) => { const r = x.getBoundingClientRect(), R = s.getBoundingClientRect(); return r.width && (r.bottom > R.bottom + 1 || r.right > R.right + 1) && !x.closest('.stack') && !x.closest('.shot') && !x.closest('.shots'); }).map((x) => x.className || x.tagName).slice(0, 5));
    if (over.length) console.log('overflow s' + (i + 1), over);
    await el.screenshot({ path: DIR + names[i] + '.png' });
  }
  await b.close();
})();
