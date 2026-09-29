// THE G.O.A.T. — deterministic frame compositor.
// renderFrame(f) draws frame f of the timeline in window.TL onto the canvas.
const W = 1920, H = 1080;
const cv = document.getElementById('c');
const ctx = cv.getContext('2d');
const tmp = document.createElement('canvas'); tmp.width = W; tmp.height = H;
const tctx = tmp.getContext('2d');
let TL = null, FPS = 24;

// ---------- utils ----------
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const eOut = t => 1 - Math.pow(1 - clamp(t), 3);
const eIn = t => Math.pow(clamp(t), 3);
const eIO = t => { t = clamp(t); return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
const eBack = t => { t = clamp(t); const c1 = 2.2, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); };
function hash(n) { // integer hash -> [-1, 1)
  let h = (n | 0) ^ 0x9e3779b9;
  h = Math.imul(h ^ (h >>> 16), 0x85ebca6b); h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35); h ^= h >>> 16;
  return (h >>> 0) / 2147483648 - 1;
}
function rnd(i, s = 0) { return (hash(i * 7919 + s * 104729 + 17) + 1) / 2; }
function noise1(x, s = 0) { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash(i + s * 1000), hash(i + 1 + s * 1000), u); }
function fade(lt, dur, fi = 0, fo = 0) {
  let a = 1;
  if (fi > 0) a *= clamp(lt / fi);
  if (fo > 0) a *= clamp((dur - lt) / fo);
  return a;
}

// ---------- image cache ----------
const cache = new Map();
function img(src) {
  if (cache.has(src)) return cache.get(src);
  const im = new Image();
  const p = new Promise(res => { im.onload = () => res(im); im.onerror = () => res(null); });
  im.src = src;
  const rec = { im, p };
  cache.set(src, rec);
  if (cache.size > 400) { const k = cache.keys().next().value; cache.delete(k); }
  return rec;
}
function frameSrc(clip, t) {
  const info = TL.clips[clip];
  if (!info) return null;
  let idx = Math.floor(t * FPS) + 1;
  idx = Math.max(1, Math.min(info.frames, idx));
  return `../media/frames/${clip}/${String(idx).padStart(4, '0')}.jpg`;
}

// ---------- drawing helpers ----------
function cover(im, kb, lt, dur) {
  const iw = im.naturalWidth || im.width, ih = im.naturalHeight || im.height;
  const s0 = Math.max(W / iw, H / ih);
  const p = dur > 0 ? clamp(lt / dur) : 0;
  const k = kb || {};
  const z = lerp(k.z0 ?? 1, k.z1 ?? (k.z0 ?? 1), k.ease === 'lin' ? p : eIO(p));
  const x = lerp(k.x0 ?? 0, k.x1 ?? (k.x0 ?? 0), eIO(p)), y = lerp(k.y0 ?? 0, k.y1 ?? (k.y0 ?? 0), eIO(p));
  const s = s0 * z, dw = iw * s, dh = ih * s;
  ctx.drawImage(im, (W - dw) / 2 + x * W, (H - dh) / 2 + y * H, dw, dh);
}
function strokeText(txt, x, y, o = {}) {
  ctx.save();
  ctx.font = `${o.weight || ''} ${o.size || 120}px ${o.font || 'Luckiest'}`;
  ctx.textAlign = o.align || 'center'; ctx.textBaseline = 'middle';
  ctx.lineJoin = 'round';
  if (o.shadow !== false) { ctx.shadowColor = 'rgba(0,0,0,.65)'; ctx.shadowOffsetX = 0; ctx.shadowOffsetY = (o.size || 120) * .08; ctx.shadowBlur = (o.size || 120) * .15; }
  if (o.stroke !== 0) { ctx.lineWidth = o.stroke ?? (o.size || 120) * .16; ctx.strokeStyle = o.strokeColor || '#000'; ctx.strokeText(txt, x, y); }
  ctx.shadowColor = 'transparent';
  ctx.fillStyle = o.fill || '#fff';
  ctx.fillText(txt, x, y);
  ctx.restore();
}
function pop(lt, d = .28) { return lt < 0 ? 0 : lt < d ? eBack(lt / d) : 1; }
function roundRect(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }

// wobbly xkcd line
function wline(x1, y1, x2, y2, seed, amp = 2.2) {
  const n = Math.max(2, Math.floor(Math.hypot(x2 - x1, y2 - y1) / 18));
  const dx = x2 - x1, dy = y2 - y1, len = Math.hypot(dx, dy) || 1, nx = -dy / len, ny = dx / len;
  ctx.beginPath();
  for (let i = 0; i <= n; i++) {
    const t = i / n, w = (i === 0 || i === n) ? 0 : (noise1(i * .7, seed) * amp);
    const px = x1 + dx * t + nx * w, py = y1 + dy * t + ny * w;
    i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
  }
  ctx.stroke();
}
function wcircle(cx, cy, r, seed, frac = 1) {
  ctx.beginPath();
  const n = 40;
  for (let i = 0; i <= n * frac; i++) {
    const a = i / n * Math.PI * 2, rr = r + noise1(i * .5, seed) * 1.8;
    const px = cx + Math.cos(a) * rr, py = cy + Math.sin(a) * rr;
    i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
  }
  ctx.stroke();
}
function wpoly(pts, seed, closed = true) {
  for (let i = 0; i < pts.length - (closed ? 0 : 1); i++) {
    const a = pts[i], b = pts[(i + 1) % pts.length];
    wline(a[0], a[1], b[0], b[1], seed + i);
  }
}

// ---------- particles ----------
function particles(kind, lt, o = {}) {
  const N = o.n || 160;
  ctx.save();
  for (let i = 0; i < N; i++) {
    const r1 = rnd(i, 1), r2 = rnd(i, 2), r3 = rnd(i, 3), r4 = rnd(i, 4);
    if (kind === 'snow') {
      const sp = 40 + r3 * 90, sz = 1.5 + r4 * 4.5;
      const x = ((r1 * W + Math.sin(lt * (.5 + r2) + i) * 40 + lt * 15) % W + W) % W;
      const y = ((r2 * H + lt * sp) % (H + 20)) - 10;
      ctx.globalAlpha = (o.alpha ?? .8) * (.4 + r4 * .6);
      ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(x, y, sz, 0, 7); ctx.fill();
    } else if (kind === 'embers') {
      const life = 1.5 + r3 * 2.5, age = ((lt + r1 * life) % life) / life;
      const x = r2 * W + Math.sin(age * 6 + i) * 60 + (o.wind || 0) * age * 200;
      const y = H + 20 - age * (H * (.7 + r4 * .6));
      ctx.globalAlpha = (o.alpha ?? 1) * Math.sin(age * Math.PI);
      ctx.fillStyle = r4 > .5 ? '#ffb13b' : '#ff5a1f';
      ctx.shadowColor = '#ff7a00'; ctx.shadowBlur = 12;
      ctx.beginPath(); ctx.arc(x, y, 1.5 + r3 * 3.5, 0, 7); ctx.fill();
    } else if (kind === 'confetti') {
      const cols = ['#ff2e63', '#ffd400', '#08d9d6', '#7cff4f', '#ff8a00', '#b967ff'];
      const x = ((r1 * W + Math.sin(lt * 2 + i) * 50) % W + W) % W, y = ((r2 * H * 1.2 + lt * (150 + r3 * 200)) % (H + 40)) - 20;
      ctx.globalAlpha = o.alpha ?? 1;
      ctx.save(); ctx.translate(x, y); ctx.rotate(lt * (2 + r4 * 6) + i); ctx.scale(1, Math.cos(lt * 5 + i));
      ctx.fillStyle = cols[i % cols.length]; ctx.fillRect(-7, -4, 14, 8); ctx.restore();
    } else if (kind === 'sparks') { // radial burst from center at lt=0
      const ang = r1 * Math.PI * 2, sp = 400 + r2 * 1400, t = lt;
      const x = W / 2 + Math.cos(ang) * sp * t, y = H / 2 + Math.sin(ang) * sp * t + 300 * t * t;
      ctx.globalAlpha = clamp(1 - t / (0.8 + r3));
      ctx.strokeStyle = r4 > .5 ? '#ffd27a' : '#ff6a00'; ctx.lineWidth = 2 + r3 * 3;
      ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - Math.cos(ang) * 30, y - Math.sin(ang) * 30); ctx.stroke();
    }
  }
  ctx.restore();
}

// ---------- flame shape (for title / xkcd) ----------
function flame(x, y, s, t, seed = 0) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  for (let k = 0; k < 3; k++) {
    const col = ['#ff3d00', '#ff9100', '#ffe066'][k], sc = 1 - k * .28;
    ctx.fillStyle = col; ctx.beginPath();
    const wob = noise1(t * 6 + k, seed) * 8;
    ctx.moveTo(-40 * sc, 0);
    ctx.bezierCurveTo(-50 * sc, -60 * sc, -10 * sc + wob, -80 * sc, 0 + wob, -140 * sc);
    ctx.bezierCurveTo(20 * sc + wob, -80 * sc, 55 * sc, -60 * sc, 40 * sc, 0);
    ctx.closePath(); ctx.fill();
  }
  ctx.restore();
}

// ---------- layer renderers ----------
const R = {};

R.video = async (L, lt) => {
  const st = (L.from || 0) + (L.speedRamp ? rampTime(L.speedRamp, lt) : lt * (L.speed || 1));
  const src = frameSrc(L.clip, st);
  if (!src) { ctx.fillStyle = '#222'; ctx.fillRect(0, 0, W, H); strokeText('[' + L.clip + ']', W / 2, H / 2, { size: 80, font: 'Mono' }); return; }
  const im = await img(src).p; if (!im) return;
  ctx.save();
  ctx.globalAlpha = fade(lt, L.dur, L.fi, L.fo) * (L.alpha ?? 1);
  if (L.blend) ctx.globalCompositeOperation = L.blend;
  let f = '';
  const g = L.grade || {};
  if (g.sat != null) f += `saturate(${g.sat}) `;
  if (g.con != null) f += `contrast(${g.con}) `;
  if (g.bri != null) f += `brightness(${g.bri}) `;
  if (g.sepia != null) f += `sepia(${g.sepia}) `;
  if (g.hue != null) f += `hue-rotate(${g.hue}deg) `;
  if (g.gray != null) f += `grayscale(${g.gray}) `;
  if (g.blur != null) f += `blur(${g.blur}px) `;
  ctx.filter = f || 'none';
  // shake + punch
  let sx = 0, sy = 0, pz = 1;
  if (L.shake) { const a = L.shake.amp * (L.shake.decay ? Math.exp(-lt * L.shake.decay) : 1); sx = noise1(lt * 22, 3) * a; sy = noise1(lt * 22, 9) * a; }
  for (const pt of (L.punch || [])) { const d = lt - pt; if (d >= 0 && d < .35) pz += .12 * (1 - eOut(d / .35)); }
  ctx.translate(W / 2 + sx, H / 2 + sy); ctx.scale(pz, pz); ctx.translate(-W / 2, -H / 2);
  cover(im, L.kb, lt, L.dur);
  ctx.restore();
};
function rampTime(r, lt) { // piecewise speed: [[t, speed], ...] integrate
  let st = 0, prevT = 0, sp = r[0][1];
  for (let i = 1; i < r.length; i++) {
    if (lt < r[i][0]) break;
    st += (r[i][0] - prevT) * sp; prevT = r[i][0]; sp = r[i][1];
  }
  return st + (lt - prevT) * sp;
}

R.still = async (L, lt) => {
  const im = await img(L.src).p; if (!im) return;
  ctx.save(); ctx.globalAlpha = fade(lt, L.dur, L.fi, L.fo);
  if (L.grade?.sepia) ctx.filter = `sepia(${L.grade.sepia})`;
  cover(im, L.kb, lt, L.dur); ctx.restore();
};

R.solid = (L, lt) => { ctx.save(); ctx.globalAlpha = (L.alpha ?? 1) * fade(lt, L.dur, L.fi, L.fo); ctx.fillStyle = L.color; ctx.fillRect(0, 0, W, H); ctx.restore(); };

R.flash = (L, lt) => { ctx.save(); ctx.globalAlpha = clamp(1 - lt / L.dur) * (L.alpha ?? 1); ctx.globalCompositeOperation = L.color === '#000' ? 'source-over' : 'lighter'; ctx.fillStyle = L.color || '#fff'; ctx.fillRect(0, 0, W, H); ctx.restore(); };

R.particles = (L, lt) => { ctx.save(); ctx.globalAlpha = fade(lt, L.dur, L.fi ?? .3, L.fo ?? .3); particles(L.kind, lt, L); ctx.restore(); };

R.letterbox = (L, lt) => {
  const h = (L.h ?? 138) * eIO(lt / .6) * clamp((L.dur - lt) / .6);
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, h); ctx.fillRect(0, H - h, W, h);
};

R.zoomblur = (L, lt) => { // radial zoom blur of what's drawn so far
  const k = clamp(1 - lt / L.dur) * (L.amt ?? 1);
  if (k <= 0.01) return;
  tctx.clearRect(0, 0, W, H); tctx.drawImage(cv, 0, 0);
  ctx.save();
  for (let i = 1; i <= 6; i++) {
    const s = 1 + i * .025 * k; ctx.globalAlpha = .18;
    ctx.drawImage(tmp, W / 2 - W * s / 2, H / 2 - H * s / 2, W * s, H * s);
  }
  ctx.restore();
};

R.whip = (L, lt) => { // horizontal smear
  const p = lt / L.dur, k = Math.sin(p * Math.PI);
  tctx.clearRect(0, 0, W, H); tctx.drawImage(cv, 0, 0);
  ctx.save();
  for (let i = -5; i <= 5; i++) { ctx.globalAlpha = .12 * k + (i === 0 ? 1 - k : 0); ctx.drawImage(tmp, i * 90 * k * (L.dir || 1), 0); }
  ctx.restore();
};

R.rgbsplit = (L, lt) => {
  const k = clamp(1 - lt / L.dur) * (L.amt ?? 14);
  if (k < .5) return;
  tctx.clearRect(0, 0, W, H); tctx.drawImage(cv, 0, 0);
  ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.globalAlpha = .55;
  ctx.filter = 'sepia(1) saturate(8) hue-rotate(-50deg)'; ctx.drawImage(tmp, -k, 0);
  ctx.filter = 'sepia(1) saturate(8) hue-rotate(150deg)'; ctx.drawImage(tmp, k, 0);
  ctx.restore();
};

R.vignette = (L, lt) => {
  const g = ctx.createRadialGradient(W / 2, H / 2, H * .35, W / 2, H / 2, H * .95);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(0,0,0,${L.amt ?? .55})`);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
};

// Mr Beast word pops: words [{t, text, fill, size, x, y, rot, hold}]
R.beast = (L, lt) => {
  const ws = L.words;
  for (let i = 0; i < ws.length; i++) {
    const w = ws[i], end = w.hold != null ? w.t + w.hold : (ws[i + 1] ? ws[i + 1].t : L.dur);
    if (lt < w.t || lt > end) continue;
    const d = lt - w.t, s = pop(d, .22);
    ctx.save(); ctx.translate(w.x ?? W / 2, w.y ?? H / 2); ctx.rotate((w.rot || 0) * Math.PI / 180 + Math.sin(d * 3) * .01);
    const breathe = 1 + Math.sin(d * 4) * .015;
    ctx.scale(s * breathe, s * breathe);
    strokeText(w.text, 0, 0, { size: w.size || 150, fill: w.fill || '#fff', font: w.font || 'Luckiest', stroke: w.stroke });
    ctx.restore();
  }
};

R.counter = (L, lt) => {
  const p = eOut((lt - (L.t0 || 0)) / (L.t1 - (L.t0 || 0)));
  const n = Math.round(lerp(L.from, L.to, p));
  const done = lt >= L.t1;
  const s = done ? 1 + .25 * Math.exp(-(lt - L.t1) * 6) : 1 + Math.sin(lt * 40) * .03;
  ctx.save(); ctx.translate(L.x ?? W / 2, L.y ?? H / 2 - 40); ctx.scale(s, s);
  if (done) { ctx.save(); ctx.globalAlpha = .9; ctx.translate(0, 130); flame(-250, 0, 1.6, lt, 1); flame(250, 0, 1.6, lt, 2); flame(0, 30, 2.2, lt, 3); ctx.restore(); }
  strokeText(String(n), 0, 0, { size: 380, fill: L.fill || '#ff2a2a', font: 'Luckiest', stroke: 34 });
  ctx.restore();
  if (L.label) strokeText(L.label, W / 2, (L.y ?? H / 2 - 40) + 250, { size: 90, fill: '#ffe600', stroke: 16 });
};

R.title = (L, lt) => {
  ctx.save();
  ctx.globalAlpha = fade(lt, L.dur, 0, .4);
  // fire glow backdrop
  const g = ctx.createRadialGradient(W / 2, H * .62, 50, W / 2, H * .62, 900);
  g.addColorStop(0, 'rgba(255,90,0,.55)'); g.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  const s = 1.25 - .25 * eOut(lt / 1.2) + lt * .02;
  ctx.translate(W / 2, H / 2 - 40); ctx.scale(s, s);
  ctx.font = '300px Anton'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  const grad = ctx.createLinearGradient(0, -150, 0, 150);
  grad.addColorStop(0, '#fff6c2'); grad.addColorStop(.45, '#ffb300'); grad.addColorStop(1, '#ff2d00');
  ctx.shadowColor = '#ff5a00'; ctx.shadowBlur = 60 + Math.sin(lt * 20) * 15;
  ctx.fillStyle = grad; ctx.fillText('THE G.O.A.T.', 0, 0);
  ctx.shadowBlur = 0; ctx.lineWidth = 4; ctx.strokeStyle = 'rgba(0,0,0,.6)'; ctx.strokeText('THE G.O.A.T.', 0, 0);
  ctx.restore();
  const a2 = clamp((lt - .7) / .4);
  ctx.save(); ctx.globalAlpha = a2 * fade(lt, L.dur, 0, .4);
  ctx.font = 'italic 600 64px Cormorant'; ctx.textAlign = 'center'; ctx.fillStyle = '#ffe9c4';
  ctx.fillText('Greatest Of All Tinder', W / 2, H / 2 + 150);
  ctx.font = '500 26px Inter5'; ctx.fillStyle = 'rgba(255,255,255,.75)';
  if (ctx.letterSpacing !== undefined) ctx.letterSpacing = '10px';
  ctx.fillText('A TRUE STORY  ·  GÄVLE, SWEDEN  ·  1966 – 2025', W / 2, H / 2 + 225);
  ctx.restore();
};

R.quote = (L, lt) => { // lines typed-in, elegant
  ctx.save();
  const a = fade(lt, L.dur, .01, L.fo ?? .5);
  ctx.textAlign = L.align || 'center'; ctx.textBaseline = 'middle';
  const x = L.x ?? W / 2;
  L.lines.forEach((ln, i) => {
    const t0 = ln.t ?? (i * .9), k = clamp((lt - t0) / .9);
    if (k <= 0) return;
    ctx.globalAlpha = a * eOut(k);
    ctx.font = ln.font || `italic 600 ${ln.size || 66}px Cormorant`;
    ctx.fillStyle = ln.fill || '#fff';
    ctx.shadowColor = 'rgba(0,0,0,.8)'; ctx.shadowBlur = 18;
    ctx.filter = `blur(${(1 - eOut(k)) * 8}px)`;
    ctx.fillText(ln.text, x, (L.y ?? H / 2) + (ln.dy ?? i * 84) + (1 - eOut(k)) * 20);
    ctx.filter = 'none';
  });
  ctx.restore();
};

R.subs = (L, lt) => { // [{t0,t1,text}]
  for (const s of L.lines) {
    if (lt < s.t0 || lt > s.t1) continue;
    const a = clamp((lt - s.t0) / .2) * clamp((s.t1 - lt) / .2);
    ctx.save(); ctx.globalAlpha = a; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.font = L.font || '52px Fell'; ctx.fillStyle = L.fill || '#f7e9c8';
    ctx.shadowColor = '#000'; ctx.shadowBlur = 14; ctx.shadowOffsetY = 3;
    const lines = s.text.split('\n');
    lines.forEach((ln, i) => ctx.fillText(ln, W / 2, (L.y ?? H - 190) + (i - (lines.length - 1)) * 62));
    ctx.restore();
  }
};

R.yearSlam = (L, lt) => {
  const s = lt < .18 ? lerp(3.2, 1, eOut(lt / .18)) : 1 + (lt - .18) * .03;
  const a = clamp(lt / .08) * clamp((L.dur - lt) / .15);
  ctx.save(); ctx.globalAlpha = a;
  ctx.translate(L.x ?? W / 2, L.y ?? H / 2); ctx.scale(s, s); ctx.rotate((L.rot ?? -4) * Math.PI / 180);
  strokeText(String(L.year), 0, 0, { size: L.size || 260, font: 'Anton', fill: L.fill || '#ffe600', stroke: 22 });
  ctx.restore();
};

R.lower = (L, lt) => { // lower third with tag
  const k = eOut(lt / .35), out = clamp((L.dur - lt) / .25);
  ctx.save(); ctx.globalAlpha = out;
  const x = lerp(-900, 80, k), y = L.y ?? H - 250;
  ctx.font = '800 34px Inter';
  const tagW = ctx.measureText(L.tag).width + 40;
  ctx.fillStyle = L.tagColor || '#ff1f3d'; ctx.save(); ctx.translate(x, y); ctx.transform(1, 0, -.2, 1, 0, 0); ctx.fillRect(0, 0, tagW, 56); ctx.restore();
  ctx.fillStyle = '#fff'; ctx.textBaseline = 'middle'; ctx.fillText(L.tag, x + 18, y + 29);
  ctx.font = `800 ${L.size || 76}px Inter`;
  const tw = ctx.measureText(L.title).width + 50;
  ctx.fillStyle = 'rgba(0,0,0,.82)'; ctx.fillRect(x, y + 62, tw, 108);
  ctx.fillStyle = '#fff'; ctx.fillText(L.title, x + 24, y + 118);
  if (L.sub) {
    ctx.font = '500 40px Inter5'; const sw = ctx.measureText(L.sub).width + 40;
    ctx.fillStyle = '#ffe600'; ctx.fillRect(x, y + 176, sw, 60);
    ctx.fillStyle = '#000'; ctx.fillText(L.sub, x + 20, y + 207);
  }
  ctx.restore();
};

R.tally = (L, lt) => { // top-right destroyed counter; hits: [t...]
  const n = L.base + L.hits.filter(h => lt >= h).length;
  const last = Math.max(-9, ...L.hits.filter(h => lt >= h));
  const s = 1 + .35 * Math.exp(-(lt - last) * 7);
  ctx.save(); ctx.globalAlpha = fade(lt, L.dur, .3, .3);
  ctx.fillStyle = 'rgba(0,0,0,.7)'; roundRect(W - 470, 40, 420, 120, 16); ctx.fill();
  ctx.font = '800 26px Inter'; ctx.fillStyle = '#ff5a5a'; ctx.textAlign = 'left'; ctx.fillText('GOATS DESTROYED', W - 440, 82);
  ctx.translate(W - 140, 105); ctx.scale(s, s);
  strokeText(String(n), 0, 0, { size: 84, font: 'Anton', fill: '#fff', stroke: 10 });
  ctx.restore();
  ctx.save(); ctx.globalAlpha = fade(lt, L.dur, .3, .3); flame(W - 410, 150, .28, lt, 5); ctx.restore();
};

R.stamp = (L, lt) => {
  const s = lt < .15 ? lerp(2.6, 1, eIn(lt / .15)) : 1;
  ctx.save(); ctx.globalAlpha = clamp(lt / .05) * fade(lt, L.dur, 0, .2);
  ctx.translate(L.x ?? W / 2, L.y ?? H / 2); ctx.rotate((L.rot ?? -12) * Math.PI / 180); ctx.scale(s, s);
  ctx.font = `${L.size || 110}px Anton`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  const lines = L.text.split('\n');
  const w = Math.max(...lines.map(l => ctx.measureText(l).width)) + 70, h = lines.length * (L.size || 110) * 1.08 + 40;
  ctx.strokeStyle = L.color || '#e0102a'; ctx.lineWidth = 12; roundRect(-w / 2, -h / 2, w, h, 18); ctx.stroke();
  ctx.fillStyle = L.color || '#e0102a';
  lines.forEach((l, i) => ctx.fillText(l, 0, (i - (lines.length - 1) / 2) * (L.size || 110) * 1.08));
  ctx.restore();
};

R.verdict = (L, lt) => { // court document card
  const k = eOut(lt / .5);
  ctx.save(); ctx.globalAlpha = fade(lt, L.dur, 0, .3);
  ctx.translate(W / 2 + 330, H / 2 + (1 - k) * 900); ctx.rotate(.035);
  ctx.shadowColor = 'rgba(0,0,0,.6)'; ctx.shadowBlur = 50; ctx.fillStyle = '#f4efe2'; ctx.fillRect(-420, -430, 840, 860);
  ctx.shadowBlur = 0; ctx.fillStyle = '#1a1a1a'; ctx.textAlign = 'center';
  ctx.font = '44px Fell'; ctx.fillText('GÄVLE TINGSRÄTT', 0, -350);
  ctx.font = '26px Fell'; ctx.fillText('District Court  ·  Case: The People v. A Lighter', 0, -305);
  ctx.fillRect(-360, -280, 720, 3);
  ctx.textAlign = 'left'; ctx.font = '500 30px Inter5';
  const rows = L.rows;
  rows.forEach((r, i) => {
    const a = clamp((lt - .5 - i * .55) / .3); ctx.globalAlpha = a;
    ctx.fillStyle = '#777'; ctx.font = '800 22px Inter'; ctx.fillText(r[0], -360, -220 + i * 118);
    ctx.fillStyle = '#111'; ctx.font = '500 32px Inter5';
    r[1].split('\n').forEach((ln, j) => ctx.fillText(ln, -360, -182 + i * 118 + j * 38));
  });
  ctx.restore();
};

R.blueprint = (L, lt) => {
  ctx.save(); const a = fade(lt, L.dur, .3, .3);
  ctx.globalAlpha = .35 * a; ctx.fillStyle = '#0a3d91'; ctx.fillRect(0, 0, W, H);
  ctx.globalAlpha = .35 * a; ctx.strokeStyle = '#7fd4ff'; ctx.lineWidth = 1;
  for (let x = 0; x < W; x += 60) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
  for (let y = 0; y < H; y += 60) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
  ctx.globalAlpha = a; ctx.strokeStyle = '#bfeaff'; ctx.fillStyle = '#e8f7ff'; ctx.lineWidth = 3;
  ctx.font = '700 58px Mono'; ctx.fillText('OPERATION: GOAT LIFT', 70, 110);
  ctx.font = '700 30px Mono';
  L.items.forEach((it, i) => {
    const k = clamp((lt - it.t) / .25); if (k <= 0) return;
    ctx.globalAlpha = a * k;
    ctx.fillText(it.text.slice(0, Math.ceil(it.text.length * clamp((lt - it.t) / .6))), 70, 180 + i * 50);
  });
  // target reticle on goat
  const rk = clamp((lt - .4) / .5); ctx.globalAlpha = a * rk;
  const cx = lerp(L.cx ?? 1180, L.cx1 ?? L.cx ?? 1180, clamp(lt / L.dur)), cy = lerp(L.cy ?? 640, L.cy1 ?? L.cy ?? 640, clamp(lt / L.dur)), rr = 230 + Math.sin(lt * 5) * 8;
  ctx.setLineDash([18, 12]); ctx.beginPath(); ctx.arc(cx, cy, rr, 0, 7); ctx.stroke(); ctx.setLineDash([]);
  ctx.beginPath(); ctx.moveTo(cx - rr - 40, cy); ctx.lineTo(cx - rr + 40, cy); ctx.moveTo(cx + rr - 40, cy); ctx.lineTo(cx + rr + 40, cy);
  ctx.moveTo(cx, cy - rr - 40); ctx.lineTo(cx, cy - rr + 40); ctx.moveTo(cx, cy + rr - 40); ctx.lineTo(cx, cy + rr + 40); ctx.stroke();
  ctx.font = '700 28px Mono'; ctx.fillText('TARGET: 1 GOAT (3 TONNES)', cx - 200, cy + rr + 80);
  // dotted route
  const pk = clamp((lt - 1.2) / 1.5); ctx.globalAlpha = a * pk; ctx.setLineDash([10, 14]); ctx.lineWidth = 5;
  ctx.beginPath(); ctx.moveTo(cx + 100, cy - 200); ctx.quadraticCurveTo(1650, 200, lerp(cx + 100, 1850, pk), lerp(cy - 200, 90, pk)); ctx.stroke(); ctx.setLineDash([]);
  ctx.fillText('→ STOCKHOLM', 1560, 70);
  ctx.restore();
};

R.tweet = (L, lt) => {
  const k = eBack(clamp(lt / .4));
  ctx.save(); ctx.globalAlpha = fade(lt, L.dur, 0, .2);
  ctx.translate(W / 2, H / 2 - 60); ctx.scale(k, k);
  ctx.shadowColor = 'rgba(0,0,0,.5)'; ctx.shadowBlur = 40; ctx.fillStyle = '#fff'; roundRect(-520, -170, 1040, 340, 30); ctx.fill(); ctx.shadowBlur = 0;
  // avatar goat
  ctx.fillStyle = '#e8b93a'; ctx.beginPath(); ctx.arc(-430, -85, 52, 0, 7); ctx.fill();
  ctx.fillStyle = '#d4202a'; ctx.fillRect(-470, -70, 80, 14);
  ctx.textAlign = 'left'; ctx.fillStyle = '#0f1419'; ctx.font = '800 38px Inter'; ctx.fillText('Gävlebocken', -355, -100);
  ctx.fillStyle = '#1d9bf0'; ctx.beginPath(); ctx.arc(-355 + ctx.measureText('Gävlebocken').width + 26, -112, 15, 0, 7); ctx.fill();
  ctx.fillStyle = '#536471'; ctx.font = '500 32px Inter5'; ctx.fillText('@Gavlebocken · 23:46', -355, -55);
  ctx.fillStyle = '#0f1419'; ctx.font = '500 76px Inter5'; ctx.fillText(L.text.slice(0, Math.ceil(L.text.length * clamp((lt - .5) / .6))), -440, 70);
  ctx.restore();
  // clock
  if (L.clockT != null && lt > L.clockT) {
    const p = clamp((lt - L.clockT) / (L.clockD || 2));
    const mins = 46 + Math.floor(p * 10);
    ctx.save(); ctx.globalAlpha = fade(lt, L.dur, 0, .2);
    const s = 1 + (p >= 1 ? .3 * Math.exp(-(lt - L.clockT - (L.clockD || 2)) * 6) : 0);
    ctx.translate(W / 2, H - 170); ctx.scale(s, s);
    strokeText(`23:${mins}`, 0, 0, { size: 150, font: 'Mono', weight: 700, fill: p >= 1 ? '#ff2a2a' : '#fff', stroke: 14 });
    ctx.restore();
  }
};

R.checks = (L, lt) => { // year checklist
  L.items.forEach((it, i) => {
    const d = lt - it.t; if (d < 0) return;
    const s = pop(d, .25);
    const x = L.x0 + i * L.dx, y = L.y;
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    strokeText(it.year, 0, 0, { size: 96, font: 'Anton', fill: '#fff', stroke: 12 });
    ctx.translate(0, 110);
    ctx.strokeStyle = '#000'; ctx.lineWidth = 26; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    const chk = () => { ctx.beginPath(); ctx.moveTo(-40, 0); ctx.lineTo(-10, 32); ctx.lineTo(48, -38); ctx.stroke(); };
    chk(); ctx.strokeStyle = '#27e35a'; ctx.lineWidth = 14; chk();
    ctx.restore();
  });
};

R.wanted = (L, lt) => {
  L.posters.forEach((p, i) => {
    const d = lt - p.t; if (d < 0) return;
    const k = eBack(clamp(d / .45));
    const rec = img(p.src); if (!rec.im.complete) return;
    ctx.save(); ctx.globalAlpha = fade(lt, L.dur, 0, .3);
    ctx.translate(p.x, lerp(H + 500, p.y, k)); ctx.rotate(p.rot * Math.PI / 180);
    ctx.shadowColor = 'rgba(0,0,0,.6)'; ctx.shadowBlur = 40; ctx.fillStyle = '#e9d7ae'; ctx.fillRect(-300, -400, 600, 800); ctx.shadowBlur = 0;
    ctx.fillStyle = '#2b1a0e'; ctx.textAlign = 'center'; ctx.font = '120px Anton'; ctx.fillText('WANTED', 0, -270);
    ctx.save(); ctx.beginPath(); ctx.rect(-240, -220, 480, 400); ctx.clip();
    ctx.filter = 'sepia(.7) contrast(1.1)';
    const [sx, sy, sw, sh] = p.crop; ctx.drawImage(rec.im, sx, sy, sw, sh, -240, -220, 480, 400);
    ctx.restore(); ctx.strokeStyle = '#2b1a0e'; ctx.lineWidth = 6; ctx.strokeRect(-240, -220, 480, 400);
    ctx.font = '54px Anton'; ctx.fillText(p.name, 0, 250);
    ctx.font = '30px Fell'; ctx.fillText(p.crime, 0, 305); ctx.fillText(p.crime2 || '', 0, 345);
    ctx.restore();
  });
};

R.credits = (L, lt) => {
  ctx.save(); ctx.textAlign = 'center';
  const y0 = H + 40 - lt * (L.speed || 110);
  let y = y0;
  for (const row of L.rows) {
    if (row.gap) { y += row.gap; continue; }
    ctx.font = row.big ? '130px Anton' : row.head ? '800 34px Inter' : '500 54px Inter5';
    ctx.fillStyle = row.head ? '#ffb300' : row.big ? '#fff' : '#eee';
    if (y > -100 && y < H + 100) ctx.fillText(row.text, W / 2, y);
    y += row.big ? 160 : row.head ? 58 : 80;
  }
  ctx.restore();
};

R.caption = (L, lt) => { // generic text
  const a = fade(lt, L.dur, L.fi ?? .15, L.fo ?? .2);
  const k = L.pop ? pop(lt, .25) : 1;
  ctx.save(); ctx.globalAlpha = a; ctx.translate(L.x ?? W / 2, L.y ?? H / 2); ctx.scale(k, k); ctx.rotate((L.rot || 0) * Math.PI / 180);
  if (L.box) {
    ctx.font = L.font; const lines = L.text.split('\n');
    const w = Math.max(...lines.map(l => ctx.measureText(l).width)) + 60, lh = L.lh || 70;
    ctx.fillStyle = L.box; ctx.fillRect(-w / 2 + (L.align === 'left' ? w / 2 - 30 : 0), -lh * .8, w, lines.length * lh + 20);
  }
  ctx.font = L.font || '800 60px Inter'; ctx.textAlign = L.align || 'center'; ctx.textBaseline = 'middle';
  ctx.fillStyle = L.fill || '#fff';
  if (L.shadow !== false) { ctx.shadowColor = 'rgba(0,0,0,.85)'; ctx.shadowBlur = 16; }
  if (L.ls && ctx.letterSpacing !== undefined) ctx.letterSpacing = L.ls;
  L.text.split('\n').forEach((l, i) => ctx.fillText(l, 0, i * (L.lh || 70)));
  ctx.restore();
};

R.seal = (L, lt) => { // red chinese seal
  const s = lt < .2 ? lerp(2, 1, eIn(lt / .2)) : 1;
  ctx.save(); ctx.globalAlpha = .9 * fade(lt, L.dur, 0, .4); ctx.translate(L.x, L.y); ctx.scale(s, s); ctx.rotate(-.05);
  ctx.fillStyle = '#b3121b'; roundRect(-70, -70, 140, 140, 12); ctx.fill();
  ctx.fillStyle = '#f5e6c8'; ctx.font = '800 38px Inter'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText('GOAT', 0, -22); ctx.fillText('道', 0, 28);
  ctx.restore();
};

R.grad = (L, lt) => { // dark band at the bottom for legibility
  ctx.save(); ctx.globalAlpha = fade(lt, L.dur, L.fi, L.fo);
  const g = ctx.createLinearGradient(0, H * .5, 0, H);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,.85)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore();
};

R.match = (L, lt) => { // a single struck match in the dark
  const k = eOut(lt / .25);
  ctx.save();
  const g = ctx.createRadialGradient(W / 2, H / 2 + 40, 5, W / 2, H / 2 + 40, 420 * k + 20);
  g.addColorStop(0, 'rgba(255,170,60,.55)'); g.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = '#e8d2a8'; ctx.fillRect(W / 2 - 5, H / 2 + 60, 10, 260);
  ctx.fillStyle = '#7a1b10'; ctx.beginPath(); ctx.ellipse(W / 2, H / 2 + 60, 11, 16, 0, 0, 7); ctx.fill();
  ctx.shadowColor = '#ffae00'; ctx.shadowBlur = 50;
  flame(W / 2, H / 2 + 62, 1.0 * k, lt, 4);
  ctx.restore();
};

// ---------- FLAMETASTIC VFX ----------
// procedural particle fire: additive gradient blobs rising along a baseline
R.fire = (L, lt) => {
  const N = L.n || 280, x0 = L.x0 ?? 0, x1 = L.x1 ?? W, by = L.y ?? H + 40, hh = L.h ?? 460, sz = L.size ?? 70;
  const k = fade(lt, L.dur, L.fi ?? .3, L.fo ?? .5) * (L.intensity ?? 1);
  if (k <= 0) return;
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < N; i++) {
    const r1 = rnd(i, 11), r2 = rnd(i, 12), r3 = rnd(i, 13), life = .7 + r3 * 1.1;
    const age = ((lt + r1 * life) % life) / life;
    const bx = x0 + r2 * (x1 - x0);
    const x = bx + noise1(lt * 2.2 + i, 7) * 55 * age + (L.wind || 0) * age * 120;
    const y = by - age * hh * (.55 + r1 * .7);
    const rad = sz * (1.1 - age * .8) * (.6 + r3 * .7);
    const a = Math.pow(1 - age, 1.4) * .42 * k;
    const c = age < .18 ? '255,240,190' : age < .45 ? '255,165,40' : '235,70,12';
    const g = ctx.createRadialGradient(x, y, 0, x, y, rad);
    g.addColorStop(0, `rgba(${c},${a})`); g.addColorStop(1, `rgba(${c},0)`);
    ctx.fillStyle = g; ctx.fillRect(x - rad, y - rad, rad * 2, rad * 2);
  }
  // hot glow at the base
  const gg = ctx.createLinearGradient(0, by - hh * .9, 0, by);
  gg.addColorStop(0, 'rgba(255,90,0,0)'); gg.addColorStop(1, `rgba(255,110,10,${.35 * k})`);
  ctx.fillStyle = gg; ctx.fillRect(x0, by - hh * .9, x1 - x0, hh * .9);
  ctx.restore();
};

// expanding fire shockwave ring + core flash
R.shock = (L, lt) => {
  const p = clamp(lt / L.dur), cx = L.x ?? W / 2, cy = L.y ?? H / 2, R0 = (L.r ?? 1300) * eOut(p);
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  const core = ctx.createRadialGradient(cx, cy, 0, cx, cy, 500 * (1 - p) + 50);
  core.addColorStop(0, `rgba(255,250,220,${.9 * (1 - p)})`); core.addColorStop(1, 'rgba(255,120,0,0)');
  ctx.fillStyle = core; ctx.fillRect(0, 0, W, H);
  for (let k = 0; k < 3; k++) {
    ctx.strokeStyle = `rgba(${k ? '255,140,20' : '255,230,160'},${(1 - p) * (.9 - k * .25)})`;
    ctx.lineWidth = (60 - k * 18) * (1 - p) + 4; ctx.shadowColor = '#ff6a00'; ctx.shadowBlur = 60;
    ctx.beginPath(); ctx.ellipse(cx, cy, R0 * (1 - k * .06), R0 * .42 * (1 - k * .06), 0, 0, 7); ctx.stroke();
  }
  ctx.restore();
};

// heat-haze + orange grade over whatever is below
R.heat = (L, lt) => {
  const k = fade(lt, L.dur, L.fi ?? .3, L.fo ?? .3) * (L.amt ?? 1);
  tctx.clearRect(0, 0, W, H); tctx.drawImage(cv, 0, 0);
  ctx.save();
  for (let y = 0; y < H; y += 24) { // wobble horizontal strips
    const dx = Math.sin(y * .05 + lt * 9) * 5 * k;
    ctx.drawImage(tmp, 0, y, W, 24, dx, y, W, 24);
  }
  ctx.globalCompositeOperation = 'overlay'; ctx.globalAlpha = .35 * k;
  ctx.fillStyle = '#ff5a00'; ctx.fillRect(0, 0, W, H);
  ctx.restore();
};

// ---------- v3 MOTION GRAPHICS ----------
function sil(kind, x, y, h, col) { // simple flat silhouettes standing on (x, y), height h px
  ctx.save(); ctx.fillStyle = col; ctx.strokeStyle = col; ctx.lineCap = 'round';
  if (kind === 'human') {
    ctx.beginPath(); ctx.arc(x, y - h * .9, h * .1, 0, 7); ctx.fill();
    ctx.lineWidth = h * .12; ctx.beginPath(); ctx.moveTo(x, y - h * .78); ctx.lineTo(x, y - h * .42);
    ctx.moveTo(x, y - h * .45); ctx.lineTo(x - h * .12, y); ctx.moveTo(x, y - h * .45); ctx.lineTo(x + h * .12, y);
    ctx.moveTo(x, y - h * .72); ctx.lineTo(x - h * .18, y - h * .45); ctx.moveTo(x, y - h * .72); ctx.lineTo(x + h * .18, y - h * .45); ctx.stroke();
  } else if (kind === 'giraffe') {
    ctx.lineWidth = h * .05;
    ctx.fillRect(x - h * .2, y - h * .5, h * .38, h * .18);
    for (const dx of [-.17, -.1, .08, .15]) { ctx.beginPath(); ctx.moveTo(x + dx * h, y - h * .34); ctx.lineTo(x + dx * h, y); ctx.stroke(); }
    ctx.lineWidth = h * .06; ctx.beginPath(); ctx.moveTo(x + h * .14, y - h * .48); ctx.lineTo(x + h * .26, y - h * .92); ctx.stroke();
    ctx.beginPath(); ctx.ellipse(x + h * .31, y - h * .93, h * .08, h * .04, .3, 0, 7); ctx.fill();
  } else if (kind === 'bus') {
    ctx.fillRect(x - h * .9, y - h * .95, h * 1.8, h * .88);
    ctx.fillStyle = 'rgba(0,0,0,.35)';
    for (let r = 0; r < 2; r++) for (let c = 0; c < 6; c++) ctx.fillRect(x - h * .8 + c * h * .28, y - h * .85 + r * h * .4, h * .2, h * .22);
    ctx.fillStyle = col; ctx.beginPath(); ctx.arc(x - h * .55, y - h * .06, h * .1, 0, 7); ctx.arc(x + h * .55, y - h * .06, h * .1, 0, 7); ctx.fill();
  }
  ctx.restore();
}

// measuring tape next to the goat + comparison silhouettes
R.ruler = (L, lt) => {
  const x = L.x ?? 1480, y0 = L.y0 ?? 930, y1 = L.y1 ?? 130, m = L.metres ?? 13, grow = eOut(lt / .9);
  const yTop = lerp(y0, y1, grow), a = fade(lt, L.dur, .1, .3);
  ctx.save(); ctx.globalAlpha = a;
  ctx.fillStyle = '#ffd400'; ctx.fillRect(x - 18, yTop, 36, y0 - yTop);
  ctx.fillStyle = '#111'; ctx.font = '700 22px Mono'; ctx.textAlign = 'left';
  for (let i = 0; i <= m; i++) {
    const yy = y0 - (y0 - y1) * i / m; if (yy < yTop) break;
    ctx.fillRect(x - 18, yy - 2, i % 5 === 0 ? 36 : 20, 4);
    if (i % 5 === 0 && i) ctx.fillText(String(i), x - 14, yy + 22);
  }
  if (grow > .98) {
    const k = pop(lt - .9, .3);
    ctx.save(); ctx.translate(x + 60, y1 + 20); ctx.scale(k, k);
    strokeText(`${m} METRES`, 0, 0, { size: 90, font: 'Anton', fill: '#ffd400', align: 'left', stroke: 12 }); ctx.restore();
  }
  (L.items || []).forEach((it, i) => {
    const k = clamp((lt - it.t) / .35); if (k <= 0) return;
    const hpx = (y0 - y1) * it.m / m;
    ctx.save(); ctx.globalAlpha = a * k; ctx.translate(0, (1 - eBack(k)) * 60);
    sil(it.kind, it.x, y0, hpx, '#ffffff');
    ctx.font = '800 30px Inter'; ctx.fillStyle = '#fff'; ctx.textAlign = 'center';
    ctx.shadowColor = '#000'; ctx.shadowBlur = 12;
    ctx.fillText(it.label, it.x, y0 + 50);
    ctx.restore();
  });
  ctx.restore();
};

// 60 goats, 43 ignite
function goatIcon(x, y, s, state, lt, seed) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  const burnt = state > 0;
  ctx.fillStyle = burnt ? '#6b5448' : '#f2c14e'; ctx.strokeStyle = burnt ? '#6b5448' : '#f2c14e';
  ctx.fillRect(-30, -22, 60, 24);
  ctx.lineWidth = 7; ctx.lineCap = 'round';
  for (const lx of [-24, -12, 12, 24]) { ctx.beginPath(); ctx.moveTo(lx, 0); ctx.lineTo(lx, 24); ctx.stroke(); }
  ctx.fillRect(22, -44, 18, 20);
  ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(28, -44); ctx.quadraticCurveTo(14, -70, -4, -56); ctx.stroke();
  if (!burnt) { ctx.fillStyle = '#d4202a'; ctx.fillRect(-4, -22, 8, 24); }
  ctx.restore();
  if (burnt && state < 1.2) { ctx.save(); ctx.globalAlpha = 1; flame(x, y + 20 * s, s * .7 * (1.3 - state), lt, seed); ctx.restore(); }
  else if (burnt) { ctx.save(); ctx.globalAlpha = .5; flame(x, y + 20 * s, s * .25, lt, seed); ctx.restore(); }
}
R.goatgrid = (L, lt) => {
  const cols = 12, rows = 5, sx = 150, sy = 150, x0 = W / 2 - (cols - 1) * sx / 2, y0 = 330;
  const order = L.order, a = fade(lt, L.dur, .15, .3);
  let n = 0;
  ctx.save(); ctx.globalAlpha = a;
  for (let i = 0; i < cols * rows; i++) {
    const r = Math.floor(i / cols), c = i % cols;
    const k = pop(lt - (r * .04 + c * .015), .3);
    const rank = order.indexOf(i), ti = rank >= 0 ? L.t0 + (L.t1 - L.t0) * (1 - Math.pow(1 - rank / 42, 1.8)) : 1e9;
    const st = lt >= ti ? (lt - ti) / .5 : 0;
    if (st > 0) n++;
    if (k > 0) goatIcon(x0 + c * sx, y0 + r * sy, 1.35 * k, st, lt, i);
  }
  ctx.restore();
  const s = n === 43 ? 1 + .3 * Math.exp(-(lt - L.t1) * 5) : 1;
  ctx.save(); ctx.globalAlpha = a; ctx.translate(W / 2, 140); ctx.scale(s, s);
  strokeText(`${n} / 60  DESTROYED`, 0, 0, { size: 110, font: 'Anton', fill: n === 43 ? '#ff2a2a' : '#fff', stroke: 14 });
  ctx.restore();
};

// Goat News Network breaking-news package
R.news = (L, lt) => {
  const k = eOut(lt / .35), a = fade(lt, L.dur, 0, .25);
  ctx.save(); ctx.globalAlpha = a;
  const y = H - 230;
  ctx.fillStyle = '#c8102e'; ctx.fillRect(lerp(-600, 60, k), y, 330, 80);
  ctx.fillStyle = '#fff'; ctx.font = '800 46px Inter'; ctx.textBaseline = 'middle';
  ctx.fillText(L.tag || 'BREAKING', lerp(-600, 60, k) + 24, y + 42);
  ctx.fillStyle = 'rgba(255,255,255,.96)'; ctx.fillRect(lerp(-2000, 60, eOut((lt - .1) / .4)), y + 80, 1800, 96);
  ctx.fillStyle = '#111'; ctx.font = '800 54px Inter';
  ctx.fillText(L.headline.slice(0, Math.ceil(L.headline.length * clamp((lt - .35) / .5))), 90, y + 130);
  // ticker
  ctx.fillStyle = '#111'; ctx.fillRect(0, H - 54, W, 54);
  ctx.fillStyle = '#ffd400'; ctx.fillRect(0, H - 54, 210, 54);
  ctx.fillStyle = '#111'; ctx.font = '800 30px Inter'; ctx.fillText('GNN', 60, H - 26);
  ctx.save(); ctx.beginPath(); ctx.rect(210, H - 54, W - 210, 54); ctx.clip();
  ctx.fillStyle = '#fff'; ctx.font = '500 30px Inter5';
  const tick = (L.ticker || '') + '   •   ';
  const tw = ctx.measureText(tick).width, off = (lt * 220) % tw;
  for (let x = 230 - off; x < W; x += tw) ctx.fillText(tick, x, H - 26);
  ctx.restore();
  // live bug
  ctx.fillStyle = '#c8102e'; roundRect(W - 230, 50, 170, 56, 8); ctx.fill();
  ctx.fillStyle = '#fff'; ctx.font = '800 32px Inter'; ctx.fillText('● LIVE', W - 210, 80);
  ctx.restore();
};

// slanted colour-bar wipe (covers the cut at the midpoint)
R.wipe = (L, lt) => {
  const p = clamp(lt / L.dur), cols = L.colors || ['#ffd400', '#ff2a2a', '#111'];
  ctx.save();
  cols.forEach((c, i) => {
    const q = eIO(clamp(p * 1.4 - i * .12));
    const x = lerp(-W * 1.6, W * 1.3, q) * (L.dir || 1);
    ctx.fillStyle = c; ctx.save(); ctx.translate(x + (L.dir === -1 ? W : 0), 0); ctx.transform(1, 0, -.35, 1, 0, 0);
    ctx.fillRect(0, 0, W * .9, H); ctx.restore();
  });
  ctx.restore();
};

// ---------- XKCD "What If" ----------
function stick(x, y, s, seed, o = {}) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.lineWidth = 4 / s * s; ctx.strokeStyle = '#111'; ctx.lineCap = 'round';
  wcircle(0, -120, 22, seed);
  wline(0, -98, 0, -30, seed + 1);
  wline(0, -30, -20, 20, seed + 2); wline(0, -30, 20, 20, seed + 3);
  const ar = o.point ? [[0, -80, 55, -110]] : [[0, -80, -30, -45]];
  wline(0, -80, 30, -45, seed + 4); wline(...ar[0], seed + 5);
  if (o.hat) { wline(-26, -140, 26, -140, seed + 6); wline(-16, -140, -16, -160, seed + 7); wline(16, -140, 16, -160, seed + 8); wline(-16, -160, 16, -160, seed + 9); }
  ctx.restore();
}
function xgoat(x, y, s, seed, o = {}) { // straw goat or terrier
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.strokeStyle = '#111'; ctx.lineWidth = 4 / s; ctx.lineCap = 'round';
  ctx.fillStyle = o.fill || '#f2cf63';
  ctx.beginPath(); ctx.rect(-90, -110, 180, 70); ctx.fill();
  wpoly([[-90, -110], [90, -110], [90, -40], [-90, -40]], seed);
  for (const lx of [-75, -45, 45, 75]) wline(lx, -40, lx, 30, seed + lx);
  ctx.beginPath(); ctx.rect(70, -175, 60, 55); ctx.fill(); wpoly([[70, -175], [130, -175], [130, -120], [70, -120]], seed + 3);
  wline(80, -110, 95, -40, seed + 4);
  if (o.terrier) {
    wline(75, -175, 60, -140, seed + 5); wline(125, -175, 140, -140, seed + 6); // floppy ears
    wline(-90, -105, -120, -140, seed + 7); // tail up
    ctx.fillStyle = '#111'; ctx.beginPath(); ctx.arc(128, -150, 5, 0, 7); ctx.fill();
  } else {
    ctx.beginPath(); ctx.moveTo(85, -175); ctx.quadraticCurveTo(45, -265, -15, -215); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(112, -175); ctx.quadraticCurveTo(80, -280, 15, -238); ctx.stroke();
    ctx.fillStyle = '#111'; ctx.beginPath(); ctx.arc(115, -155, 4, 0, 7); ctx.fill();
    wline(125, -120, 118, -95, seed + 12); wline(112, -120, 108, -98, seed + 13);
    ctx.strokeStyle = '#d4202a'; ctx.lineWidth = 8 / s; wline(0, -110, 0, -40, seed + 9, 1);
  }
  ctx.restore();
}
R.xkcd = (L, lt) => {
  const seed = Math.floor(lt * 8); // gentle line boil
  ctx.save();
  ctx.fillStyle = '#fbfaf5'; ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = '#111'; ctx.fillStyle = '#111'; ctx.lineWidth = 4; ctx.lineCap = 'round';
  ctx.font = '96px Xkcd'; ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left';
  ctx.fillText('WHAT IF?', 90, 150);
  ctx.font = '44px Xkcd'; ctx.fillText('...you tried to protect a straw goat?', 100, 215);
  wline(90, 240, 1830, 240, 77 + seed);
  const tt = L.tt;
  if (lt < tt.p1End) {
    stick(300, 820, 2.4, 11 + seed, { point: true });
    ctx.font = '60px Xkcd'; ctx.fillText('SWEDEN TRIED:', 640, 360);
    L.list.forEach((txt, i) => {
      const ti = tt.list[i]; if (lt < ti) return;
      const y = 460 + i * 115;
      ctx.lineWidth = 4; wpoly([[660, y - 45], [715, y - 45], [715, y + 10], [660, y + 10]], 30 + i + seed);
      ctx.font = '76px Xkcd'; ctx.fillText(txt, 750, y);
      if (lt > ti + .3) { ctx.lineWidth = 7; wline(668, y - 20, 685, y, 50 + i); wline(685, y, 712, y - 55, 60 + i); }
      if (lt > ti + .5) { flame(1330, y + 10, .45, lt, i); ctx.font = '56px Xkcd'; ctx.fillStyle = '#c00'; ctx.fillText('(burned anyway)', 1350, y); ctx.fillStyle = '#111'; }
    });
  } else if (lt < tt.p2End) {
    ctx.textAlign = 'center';
    if (lt < tt.ice) {
      xgoat(420, 850, 2.2, 5 + seed, {});
      ctx.font = '60px Xkcd'; ctx.fillText('BEFORE', 480, 950);
      if (lt > tt.arrow) {
        ctx.font = '160px Xkcd'; ctx.fillText('→', 960, 600);
        ctx.font = '48px Xkcd'; ctx.fillText('AIRCRAFT', 960, 690); ctx.fillText('FIRE RETARDANT', 960, 745);
      }
      if (lt > tt.terrier) {
        xgoat(1400, 850, 2.2, 9 + seed, { terrier: true, fill: '#8a5a2b' });
        ctx.font = '60px Xkcd'; ctx.fillText('AFTER', 1460, 950);
        ctx.font = '58px Xkcd'; ctx.fillText('"LIKE A BROWN TERRIER"', 1200, 330);
        ctx.font = '36px Xkcd'; ctx.fillText('- the Goat Committee, actually', 1230, 380);
        ctx.lineWidth = 3; wline(1420, 400, 1560, 470, 88);
      }
    } else {
      const melt = clamp((lt - tt.melt) / 1.2);
      xgoat(740, 850, 1.9, 13 + seed, {});
      ctx.save(); ctx.globalAlpha = 1 - melt; ctx.strokeStyle = '#3aa0ff'; ctx.lineWidth = 6; ctx.fillStyle = 'rgba(120,200,255,.35)';
      ctx.fillRect(430, 300, 640, 600); wpoly([[430, 300], [1070, 300], [1070, 900], [430, 900]], 21 + seed); ctx.restore();
      if (melt > 0) { ctx.fillStyle = 'rgba(120,200,255,.5)'; ctx.beginPath(); ctx.ellipse(760, 880, 420 * melt, 45 * melt, 0, 0, 7); ctx.fill(); }
      ctx.fillStyle = '#111'; ctx.font = '96px Xkcd'; ctx.fillText(melt > 0 ? 'ICE (MELTED)' : 'ICE', 1450, 600);
    }
  } else {
    
    // restaurant
    ctx.lineWidth = 5; wpoly([[1050, 380], [1750, 380], [1750, 900], [1050, 900]], 40 + seed);
    wline(1020, 380, 1400, 280, 41 + seed); wline(1400, 280, 1780, 380, 42 + seed);
    ctx.font = '64px Xkcd'; ctx.textAlign = 'center'; ctx.fillText('RESTAURANT', 1400, 360);
    ctx.fillStyle = '#fff4c4'; ctx.fillRect(1120, 470, 560, 280); ctx.fillStyle = '#111';
    wpoly([[1120, 470], [1680, 470], [1680, 750], [1120, 750]], 43 + seed);
    stick(1290, 760, 1.25, 44 + seed, { hat: true }); stick(1500, 760, 1.25, 45 + seed, { hat: true });
    ctx.font = '44px Xkcd'; ctx.fillText('mmm, soup', 1395, 520);
    // thermometer
    ctx.font = '90px Xkcd'; ctx.fillStyle = '#1d6fd1'; ctx.fillText('-20°C', 800, 330); ctx.fillStyle = '#111';
    // lonely goat
    xgoat(380, 920, 2.1, 46 + seed, {});
    if (lt > tt.dots) { ctx.font = '110px Xkcd'; ctx.fillText('...', 640, 380); }
    if (lt > tt.fire) { flame(250, 900, 1.5, lt, 1); flame(420, 900, 1.9, lt, 2); flame(600, 900, 1.4, lt, 3); }
  }
  ctx.restore();
};

// global grain
function grain(f, amt) {
  ctx.save(); ctx.globalAlpha = amt; ctx.globalCompositeOperation = 'overlay';
  const s = 3;
  for (let i = 0; i < 1400; i++) {
    const x = rnd(i, f) * W, y = rnd(i + 99991, f) * H, v = rnd(i, f + 7) > .5 ? 255 : 0;
    ctx.fillStyle = `rgb(${v},${v},${v})`; ctx.fillRect(x, y, s, s);
  }
  ctx.restore();
}

// ---------- main ----------
window.loadTL = async (tl) => { TL = tl; FPS = tl.fps; await document.fonts.ready; return true; };
window.renderFrame = async (f) => {
  const t = f / FPS;
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.filter = 'none'; ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  const act = TL.layers.filter(L => t >= L.start && t < L.start + L.dur);
  // preload video frames for this + next frames
  await Promise.all(act.filter(L => L.type === 'video').map(L => {
    const lt = t - L.start, st = (L.from || 0) + (L.speedRamp ? rampTime(L.speedRamp, lt) : lt * (L.speed || 1));
    const a = frameSrc(L.clip, st); if (!a) return null;
    img(frameSrc(L.clip, st + 2 / FPS));
    return img(a).p;
  }));
  await Promise.all(act.filter(L => L.type === 'still' || L.type === 'wanted').flatMap(L => L.type === 'still' ? [img(L.src).p] : L.posters.map(p => img(p.src).p)));
  for (const L of act) {
    ctx.save();
    try { await R[L.type](L, t - L.start); } catch (e) { console.error(L.type, e); }
    ctx.restore();
  }
  grain(f, .06);
  return true;
};
