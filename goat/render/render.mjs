// Render timeline.json to video via headless Chromium + ffmpeg.
// usage: node render.mjs <out.mp4> [--workers N] [--from s] [--to s] [--step k] [--scale 0.5]
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import url from 'node:url';

const dir = path.dirname(url.fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const out = args[0];
const tl = JSON.parse(fs.readFileSync(path.join(dir, 'timeline.json'), 'utf8'));
const fps = tl.fps, step = +opt('--step', 1), scale = +opt('--scale', 1);
const f0 = Math.round(+opt('--from', 0) * fps), f1 = Math.round(+opt('--to', tl.dur) * fps);
const workers = +opt('--workers', 3);
const frames = []; for (let f = f0; f < f1; f += step) frames.push(f);
const chunk = Math.ceil(frames.length / workers);

const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--disable-web-security'] });
const t0 = Date.now();
let done = 0;
async function work(w) {
  const mine = frames.slice(w * chunk, (w + 1) * chunk);
  if (!mine.length) return null;
  const seg = `${out}.part${w}.mp4`;
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto('file://' + path.join(dir, 'index.html'));
  await page.evaluate(t => window.loadTL(t), tl);
  const W = Math.round(1920 * scale / 2) * 2, H = Math.round(1080 * scale / 2) * 2;
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps / step), '-i', '-',
    '-vf', `scale=${W}:${H}:flags=lanczos`, '-c:v', 'libx264', '-preset', scale < 1 ? 'veryfast' : 'slow', '-crf', scale < 1 ? '26' : '17',
    '-pix_fmt', 'yuv420p', seg], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (const f of mine) {
    await page.evaluate(f => window.renderFrame(f), f);
    const buf = await page.screenshot({ type: 'jpeg', quality: 94 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (++done % 120 === 0) console.log(`${done}/${frames.length} frames, ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  return seg;
}
const segs = (await Promise.all([...Array(workers).keys()].map(work))).filter(Boolean);
await browser.close();
fs.writeFileSync(`${out}.list`, segs.map(s => `file '${path.resolve(s)}'`).join('\n'));
await new Promise(r => spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', `${out}.list`, '-c', 'copy', out], { stdio: 'inherit' }).on('close', r));
segs.forEach(s => fs.unlinkSync(s)); fs.unlinkSync(`${out}.list`);
console.log(`rendered ${frames.length} frames -> ${out} in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
