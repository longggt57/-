// video.html의 render(t)를 30fps로 한 장씩 찍어 ffmpeg로 MP4를 만듭니다.
// node docs/fiverr/video/render.js [출력.mp4]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const FPS = 30;
const out = process.argv[2] || path.join(__dirname, 'fiverr_showreel.mp4');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto('file://' + path.join(__dirname, 'video.html'), { waitUntil: 'networkidle' }); await p.waitForTimeout(1000);
  const dur = await p.evaluate(() => window.DURATION);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-r', String(FPS), out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const N = Math.round(dur * FPS);
  for (let i = 0; i < N; i++) {
    await p.evaluate((t) => render(t), i / FPS);
    const buf = await p.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    if (i % 150 === 0) console.log(`frame ${i}/${N}`);
  }
  ff.stdin.end(); await new Promise((r) => ff.on('close', r));
  await b.close(); console.log('done', out);
})();
