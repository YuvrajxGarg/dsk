// Dsk UI. Talks to Python through window.pywebview.api; Python pushes
// updates back by calling App.on(event, payload).
(function () {
  const ICONS = {
    apps: '<rect x="3.5" y="4" width="17" height="16" rx="3"/><path d="M3.5 9h17"/>',
    dev: '<path d="m8 8-4 4 4 4"/><path d="m16 8 4 4-4 4"/>',
    photos: '<rect x="3.5" y="3.5" width="17" height="17" rx="4"/><circle cx="9" cy="9" r="1.6"/><path d="m20.5 15-4-4-9 9.5"/>',
    movies: '<rect x="3.5" y="3.5" width="17" height="17" rx="3"/><path d="M8 3.5v17M16 3.5v17M3.5 9H8M3.5 15H8M16 9h4.5M16 15h4.5M8 12h8"/>',
    docs: '<path d="M7 3.5h7l4 4v11a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-13a2 2 0 0 1 2-2z"/><path d="M9 12h6M9 15.5h4"/><path d="M14 3.5v4h4"/>',
    music: '<path d="M9 18V6l10-2v12"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="16.5" cy="16" r="2.5"/><path d="M9 10l10-2"/>',
    system: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
    caches: '<path d="m12 3 9 4.5-9 4.5-9-4.5z"/><path d="m3 12 9 4.5 9-4.5"/><path d="m3 16.5 9 4.5 9-4.5"/>',
    trash: '<path d="M4 6.5h16M9 6.5V4.5h6v2M18.5 6.5l-1 13a1.5 1.5 0 0 1-1.5 1.4H8a1.5 1.5 0 0 1-1.5-1.4l-1-13"/><path d="M10 11v6M14 11v6"/>',
    gear: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
    refresh: '<path d="M20 12a8 8 0 1 1-2.4-5.7L20 8.5"/><path d="M20 3.5v5h-5"/>',
    sparkle: '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M19 17v4M17 19h4"/>',
    check: '<path d="M20 6 9 17l-5-5"/>',
    x: '<path d="M18 6 6 18M6 6l12 12"/>',
    chev: '<path d="m9 6 6 6-6 6"/>',
    reveal: '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
    alert: '<path d="M12 9v4M12 17h.01"/><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/>',
    loader: '<path d="M12 2v4M12 18v4M4.9 4.9l2.8 2.8M16.3 16.3l2.8 2.8M2 12h4M18 12h4M4.9 19.1l2.8-2.8M16.3 7.7l2.8-2.8"/>',
    download: '<path d="M12 4v11"/><path d="m7 10 5 5 5-5"/><path d="M4 20h16"/>',
    lock: '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
    bolt: '<path d="M13 2 3 14h9l-1 8 10-12h-9z"/>',
    sparkles: '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/>',
    info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
  };
  const icon = (n) => `<svg class="i" viewBox="0 0 24 24">${ICONS[n] || ''}</svg>`;
  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  document.querySelectorAll('[data-icon]').forEach((el) => {
    const svg = icon(el.dataset.icon);
    if (el.tagName === 'I') el.outerHTML = svg; else el.insertAdjacentHTML('afterbegin', svg);
  });
  // Decimal units, like Finder and the reference design.
  const gb = (n) => {
    n = +n || 0;
    if (n <= 0) return '0.0 GB';
    if (n < 1e6) return (n / 1e3).toFixed(n < 1e4 ? 1 : 0) + ' KB';
    if (n < 1e9) return (n / 1e6).toFixed(n < 1e8 ? 1 : 0) + ' MB';
    if (n < 1e12) return (n / 1e9).toFixed(1) + ' GB';
    return (n / 1e12).toFixed(2) + ' TB';
  };
  const plural = (n, w) => `${n.toLocaleString()} ${w}${n === 1 ? '' : 's'}`;
  const days = (ts) => (ts ? Math.max(0, Math.floor((Date.now() / 1000 - ts) / 86400)) : null);
  const ageText = (ts) => { const d = days(ts); return d == null ? '' : d === 0 ? 'today' : d === 1 ? 'yesterday' : d < 60 ? `${d} days ago` : d < 730 ? `${Math.round(d / 30)} months ago` : `${Math.round(d / 365)} years ago`; };

  let api = null, settings = {}, upd = null, modal = null, platform = 'darwin';
  let claude = { has_key: false, hint: '' }, wiz = null;
  let cats = [];
  let scanState = { sizes: {}, disk: { total: 0, used: 0 }, done: false, current: '' };
  let groups = [], advice = {}, summary = { safe: 0, review: 0 };
  let large = [], largeFilter = 'all';
  const sel = new Set();          // selected paths
  let selTrash = false;           // empty the Trash too
  const open = new Set();         // expanded groups
  const explains = {};            // path -> answer
  let phase = 'idle';             // idle | scanning | looking | ready | cleaning
  let tab = 'clean', hot = null, claudeState = null;
  const isWin = () => platform.startsWith('win');
  const trashName = () => (isWin() ? 'Recycle Bin' : 'Trash');

  const CAT_INFO = {
    apps: 'Apps installed on this computer.',
    dev: 'Code, toolchains, package caches and project dependencies like node_modules.',
    photos: 'Your pictures and photo libraries.',
    movies: 'Videos, screen recordings and editing projects.',
    docs: 'Documents, Desktop, Downloads and synced cloud folders.',
    music: 'Music, podcasts and audio projects.',
    system: 'The operating system, its snapshots, swap and the data apps keep for you. The system manages it.',
    caches: 'Temporary files apps rebuild when they need them.',
    trash: 'Things you have already deleted.',
  };

  // ---------------------------------------------------------------------------
  // The dot-matrix bar
  // ---------------------------------------------------------------------------
  const bar = { canvas: $('#bar'), shown: {}, cols: 0, rows: 0, seeds: null, particles: [], t0: performance.now() };
  const PITCH = 8, CELL = 5.5, PAD = 18;
  function hexA(hex, a) {
    const n = parseInt(hex.slice(1), 16);
    return `rgba(${n >> 16 & 255},${n >> 8 & 255},${n & 255},${a})`;
  }
  function sizeBar() {
    const c = bar.canvas, r = c.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
    c.width = Math.round(r.width * dpr); c.height = Math.round(r.height * dpr);
    bar.w = r.width; bar.h = r.height; bar.dpr = dpr;
    bar.cols = Math.floor((r.width - PAD * 2 + (PITCH - CELL)) / PITCH);
    bar.rows = Math.floor((r.height - PAD * 2 + (PITCH - CELL)) / PITCH);
    bar.ox = PAD + ((r.width - PAD * 2) - (bar.cols * PITCH - (PITCH - CELL))) / 2;
    bar.oy = PAD + ((r.height - PAD * 2) - (bar.rows * PITCH - (PITCH - CELL))) / 2;
    const n = bar.cols * bar.rows;
    bar.seeds = new Float32Array(n * 2);
    for (let i = 0; i < n * 2; i++) bar.seeds[i] = Math.random();
  }
  // Column spans for each category, from the shown (animated) sizes.
  function spans() {
    const total = scanState.disk.total || 1;
    let acc = 0; const out = [];
    for (const c of cats) {
      const v = bar.shown[c.key] || 0;
      const a = acc / total * bar.cols, b = (acc + v) / total * bar.cols;
      acc += v;
      const c0 = Math.round(a), c1 = Math.round(b);
      if (c1 > c0) out.push({ key: c.key, color: c.color, c0, c1 });
    }
    return out;
  }
  function drawBar(now) {
    const ctx = bar.canvas.getContext('2d');
    // ease shown sizes toward the real ones
    for (const c of cats) {
      const target = scanState.sizes[c.key] || 0, cur = bar.shown[c.key] || 0;
      bar.shown[c.key] = Math.abs(target - cur) < 1e6 ? target : cur + (target - cur) * 0.12;
    }
    ctx.setTransform(bar.dpr, 0, 0, bar.dpr, 0, 0);
    ctx.clearRect(0, 0, bar.w, bar.h);
    const t = (now - bar.t0) / 1000;
    const S = spans();
    const owner = new Int16Array(bar.cols).fill(-1);
    S.forEach((s, i) => { for (let c = s.c0; c < s.c1 && c < bar.cols; c++) owner[c] = i; });
    const lastUsed = S.length ? S[S.length - 1].c1 : 0;
    // free space: faint dots
    ctx.fillStyle = 'rgba(255,255,255,.055)';
    for (let c = lastUsed; c < bar.cols; c++) for (let r = 0; r < bar.rows; r++) ctx.fillRect(bar.ox + c * PITCH, bar.oy + r * PITCH, CELL, CELL);
    // used space: segment cells, some lit and twinkling, brighter toward each segment's right edge
    S.forEach((s, i) => {
      const dim = hot && hot !== s.key;
      const width = Math.max(1, s.c1 - s.c0);
      for (let c = s.c0; c < s.c1; c++) {
        const edge = (c - s.c0 + 1) / width;
        for (let r = 0; r < bar.rows; r++) {
          const k = (c * bar.rows + r) * 2, a = bar.seeds[k], b = bar.seeds[k + 1];
          const tw = Math.sin(t * (0.6 + b * 1.6) + a * 6.283);
          const lit = a > 0.86 - edge * 0.22 - (hot === s.key ? 0.12 : 0) || tw > 0.985 - edge * 0.05;
          let alpha = lit ? 0.95 : 0.22 + 0.16 * edge * b;
          if (dim) alpha *= 0.28;
          ctx.fillStyle = lit ? (b > 0.7 && !dim ? '#ffffff' : s.color) : s.color;
          ctx.globalAlpha = lit && b > 0.7 && !dim ? 0.85 : alpha;
          ctx.fillRect(bar.ox + c * PITCH, bar.oy + r * PITCH, CELL, CELL);
        }
      }
      ctx.globalAlpha = 1;
      // outline with glow
      const x0 = bar.ox + s.c0 * PITCH - 2.5, x1 = bar.ox + s.c1 * PITCH - (PITCH - CELL) + 2.5;
      const y0 = bar.oy - 2.5, y1 = bar.oy + bar.rows * PITCH - (PITCH - CELL) + 2.5;
      const first = i === 0, last = i === S.length - 1;
      ctx.save();
      ctx.strokeStyle = hexA(s.color, dim ? 0.3 : 0.95);
      ctx.lineWidth = 2;
      ctx.shadowColor = s.color; ctx.shadowBlur = dim ? 0 : (hot === s.key ? 22 : 12);
      ctx.beginPath();
      if (ctx.roundRect) ctx.roundRect(x0, y0, x1 - x0, y1 - y0, [first ? 12 : 3, last ? 12 : 3, last ? 12 : 3, first ? 12 : 3]);
      else ctx.rect(x0, y0, x1 - x0, y1 - y0);
      ctx.stroke();
      ctx.restore();
    });
    // the scan front: a soft white glow while measuring
    if (phase === 'scanning' && lastUsed > 0) {
      const x = bar.ox + lastUsed * PITCH;
      const g = ctx.createRadialGradient(x, bar.h / 2, 0, x, bar.h / 2, 70);
      g.addColorStop(0, 'rgba(255,255,255,.22)'); g.addColorStop(1, 'rgba(255,255,255,0)');
      ctx.fillStyle = g; ctx.fillRect(x - 70, 0, 140, bar.h);
    }
    // particles from cleared space
    if (bar.particles.length) {
      const keep = [];
      for (const p of bar.particles) {
        p.life -= 0.016; p.x += p.vx; p.y += p.vy; p.vy -= 0.02; p.vx *= 0.99;
        if (p.life <= 0) continue;
        ctx.globalAlpha = Math.min(1, p.life * 1.4);
        ctx.fillStyle = p.color;
        ctx.fillRect(p.x, p.y, CELL * p.s, CELL * p.s);
        keep.push(p);
      }
      ctx.globalAlpha = 1;
      bar.particles = keep;
    }
    requestAnimationFrame(drawBar);
  }
  function burst(moved) {
    // Dots of the cleared bytes scatter away from the end of their segment.
    const total = scanState.disk.total || 1;
    const S = spans();
    for (const [key, bytes] of Object.entries(moved || {})) {
      const s = S.find((x) => x.key === key);
      if (!s) continue;
      const cols = Math.max(1, Math.round(bytes / total * bar.cols));
      for (let c = Math.max(s.c0, s.c1 - cols); c < s.c1; c++) {
        for (let r = 0; r < bar.rows; r++) {
          if (bar.particles.length > 2500 || Math.random() > 0.55) continue;
          bar.particles.push({ x: bar.ox + c * PITCH, y: bar.oy + r * PITCH, vx: 0.6 + Math.random() * 2.4, vy: (Math.random() - 0.6) * 1.6,
            life: 0.7 + Math.random() * 0.9, s: 0.5 + Math.random() * 0.7, color: Math.random() > 0.7 ? '#fff' : s.color });
        }
      }
    }
  }
  function segAt(x) {
    const c = Math.floor((x - bar.ox) / PITCH);
    const s = spans().find((sp) => c >= sp.c0 && c < sp.c1);
    return s ? s.key : null;
  }
  bar.canvas.addEventListener('mousemove', (e) => {
    const r = bar.canvas.getBoundingClientRect();
    setHot(segAt(e.clientX - r.left), e.clientX - r.left - PAD);
  });
  bar.canvas.addEventListener('mouseleave', () => setHot(null));
  function setHot(key, x) {
    const changed = key !== hot;
    hot = key;
    const tip = $('#bar-tip');
    if (key) {
      const c = cats.find((k) => k.key === key);
      tip.innerHTML = `<b>${esc(c.label)}</b><span>${gb(scanState.sizes[key])}</span>`;
      if (x != null) tip.style.left = Math.max(40, Math.min(bar.w - 2 * PAD - 40, x)) + 'px';
      tip.classList.remove('hidden');
    } else tip.classList.add('hidden');
    if (changed) {
      document.querySelectorAll('.cat').forEach((el) => el.classList.toggle('hot', el.dataset.key === key));
      $('#cats').classList.toggle('hovering', !!key);
      renderFoot();
    }
  }

  // ---------------------------------------------------------------------------
  // Hero: numbers, categories, footer
  // ---------------------------------------------------------------------------
  function renderHead() {
    const d = scanState.disk;
    const [num, unit] = gb(d.used).split(' ');
    $('#used').textContent = `${num} ${unit}`;
    $('#of').textContent = d.total ? `of ${gb(d.total).replace(/\.0 /, ' ').replace(/^(\d+)\.\d+ GB$/, (m, a) => a + ' GB')} used` : '';
    const verb = $('#status-verb'), path = $('#status-path');
    if (phase === 'scanning') { verb.textContent = scanState.engine === 'wiztree' ? 'WizTree is measuring' : 'Calculating'; path.textContent = scanState.current || ''; }
    else if (phase === 'looking') { verb.textContent = 'Measured'; path.textContent = ''; }
    else if (phase === 'cleaning') { verb.textContent = selTrash && !cleanPaths.length ? `Emptying the ${trashName()}` : 'Clearing'; path.textContent = scanState.current || ''; }
    else if (scanState.done) {
      verb.textContent = `${gb(d.free)} free`;
      path.textContent = `Scanned in ${scanState.seconds}s${scanState.engine === 'wiztree' ? ' with WizTree' : ''}` +
        (scanState.denied_count ? ` · ${plural(scanState.denied_count, 'folder')} couldn’t be read` : '');
    } else { verb.textContent = 'Getting ready'; path.textContent = ''; }
    const rs = $('#rescan');
    rs.disabled = phase === 'scanning' || phase === 'cleaning' || phase === 'looking';
    rs.classList.toggle('spin', phase === 'scanning');
  }
  function renderCats() {
    const el = $('#cats');
    if (!el.children.length) {
      el.innerHTML = cats.map((c) => `<div class="cat" data-key="${c.key}" style="--c:${c.color}">${icon(c.key)}<span class="n">${esc(c.label)}</span><span class="s"></span></div>`).join('');
      el.querySelectorAll('.cat').forEach((row) => {
        row.onmouseenter = () => setHot(row.dataset.key, centerOf(row.dataset.key));
        row.onmouseleave = () => setHot(null);
      });
    }
    el.querySelectorAll('.cat').forEach((row) => {
      const k = row.dataset.key, v = scanState.sizes[k] || 0;
      const s = row.querySelector('.s');
      const pending = (k === 'system' && !scanState.done);
      s.textContent = pending ? '…' : gb(v).replace(' KB', ' KB');
      s.classList.toggle('zero', !pending && v < 5e7);
      row.classList.toggle('pending', pending);
    });
  }
  function centerOf(key) {
    const s = spans().find((x) => x.key === key);
    return s ? bar.ox + (s.c0 + s.c1) / 2 * PITCH - PAD : null;
  }
  function groupsFor(pred) { return groups.filter(pred); }
  function renderFoot() {
    const f = $('#hero-foot');
    if (phase === 'scanning' || phase === 'looking' || phase === 'idle') {
      f.innerHTML = `<div class="msg loader">${icon('loader')}<span>${phase === 'looking' ? 'Looking for things you can clear' : 'Measuring your disk'}</span></div>`;
      return;
    }
    if (phase === 'cleaning') {
      f.innerHTML = `<div class="msg loader">${icon('loader')}<span>${selTrash && !cleanPaths.length ? `Emptying the ${trashName()}` : (settings.use_trash ? `Moving to the ${trashName()}` : 'Deleting')}…</span></div>`;
      return;
    }
    if (hot) {
      const c = cats.find((k) => k.key === hot);
      let btn = '';
      const safe = groupsFor((g) => g.cat === hot && g.verdict === 'safe' && g.action === 'remove');
      const safeSize = safe.reduce((a, g) => a + g.size, 0);
      if (hot === 'trash' && scanState.sizes.trash > 0) btn = `<button class="btn-primary inline" data-f="empty">${icon('trash')}Empty ${trashName()}</button>`;
      else if (safeSize > 0) btn = `<button class="btn-primary inline" data-f="cat" data-cat="${hot}">${icon(hot === 'caches' ? 'caches' : 'sparkles')}Clear ${hot === 'caches' ? 'caches' : 'safe ' + c.label.toLowerCase() + ' files'} · ${gb(safeSize)}</button>`;
      let line = CAT_INFO[hot] || '';
      if (hot === 'trash') line = scanState.sizes.trash > 0 ? `The ${trashName()} is holding <b>${gb(scanState.sizes.trash)}</b> of things you’ve already deleted.` : `The ${trashName()} is empty.`;
      f.innerHTML = `<div class="msg"><span class="ci" style="color:${c.color}">${icon(hot)}</span><span>${line}</span></div>${btn}`;
      f.onclick = footClick;
      return;
    }
    const s = summary.safe, r = summary.review;
    if (s + r <= 0) {
      f.innerHTML = `<div class="msg">${icon('check')}<span>Nothing obvious to clear. Check <b>Large files</b> for big things you might not need.</span></div>`;
      return;
    }
    f.innerHTML = `<div class="msg">${icon('sparkles')}<span>You can clear <b>${gb(s)}</b> safely${r > 0 ? `, and up to ${gb(r)} more after a look` : ''}.<span class="sub">Rest on a part of the bar to see what’s in it.</span></span></div>
      ${s > 0 ? `<button class="btn-primary inline" data-f="safe">${icon('sparkles')}Clear ${gb(s)}</button>` : ''}`;
    f.onclick = footClick;
  }
  function footClick(e) {
    const b = e.target.closest('[data-f]');
    if (!b) return;
    const what = b.dataset.f;
    if (what === 'empty') confirmClean([], true);
    else if (what === 'safe') confirmClean(safePaths(), false);
    else if (what === 'cat') {
      const paths = [];
      groupsFor((g) => g.cat === b.dataset.cat && g.verdict === 'safe' && g.action === 'remove').forEach((g) => g.items.forEach((i) => paths.push(i.path)));
      confirmClean(paths, false);
    }
  }
  function safePaths() {
    const out = [];
    groups.forEach((g) => { if (g.verdict === 'safe' && g.action === 'remove') g.items.forEach((i) => out.push(i.path)); });
    return out;
  }

  // ---------------------------------------------------------------------------
  // Clean-up list
  // ---------------------------------------------------------------------------
  const VERDICT = {
    safe: ['Safe to clear', 'Rebuilt or re-downloaded when needed'],
    review: ['Look first', 'Probably fine to remove, but your call'],
    keep: ['Leave alone', 'Taking space, but not Dsk’s to remove'],
  };
  function groupState(g) {
    if (g.action === 'empty_trash') return selTrash ? 'on' : '';
    if (g.action !== 'remove' || !g.items.length) return '';
    let n = 0;
    g.items.forEach((i) => { if (sel.has(i.path)) n++; });
    return n === 0 ? '' : n === g.items.length ? 'on' : 'part';
  }
  function adviceHtml(path) {
    const a = advice[path];
    if (!a) return '';
    const v = { safe: 'Safe', review: 'Look first', keep: 'Keep' }[a.verdict];
    return `<span class="advice v-${a.verdict}"><i></i><span><em>Claude: ${v}.</em> ${esc(a.reason)}</span></span>`;
  }
  function explainHtml(path) {
    const x = explains[path];
    if (!x) return '';
    if (x.phase === 'thinking') return `<div class="explain">${icon('sparkle')} Claude is looking at this…</div>`;
    if (x.phase === 'failed') return `<div class="explain">${esc(x.error)}</div>`;
    const v = { safe: 'Safe to remove', review: 'Your call', keep: 'Keep it' }[x.verdict] || '';
    return `<div class="explain"><b>${esc(x.what)}</b> ${esc(v)}: ${esc(x.reason)}${x.how ? ' ' + esc(x.how) : ''}</div>`;
  }
  function itemHtml(i, checkable) {
    return `<div class="item" data-path="${esc(i.path)}">
        ${checkable ? `<button class="chk ${sel.has(i.path) ? 'on' : ''}" data-a="item">${icon('check')}</button>` : ''}
        <div class="t"><b>${esc(i.name)}</b><code>${esc(i.show)}</code>${i.note ? `<span class="note">${esc(i.note)}</span>` : ''}${adviceHtml(i.path)}</div>
        <div class="acts"><button class="btn-icon" data-a="explain" title="What is this? (asks Claude)">${icon('sparkle')}</button>
          <button class="btn-icon" data-a="reveal" title="Show in ${isWin() ? 'Explorer' : 'Finder'}">${icon('reveal')}</button></div>
        <span class="sz">${gb(i.size)}</span>
      </div>${explainHtml(i.path)}`;
  }
  function renderClean() {
    const el = $('#clean');
    if (!groups.length) {
      el.innerHTML = phase === 'ready' ? `<div class="empty"><b>All clear</b>Nothing Dsk knows how to clear safely right now.</div>`
        : `<div class="empty"><b>Measuring</b>Dsk lists what you can clear as soon as the scan is done.</div>`;
      return;
    }
    let html = '';
    for (const v of ['safe', 'review', 'keep']) {
      const gs = groups.filter((g) => g.verdict === v);
      if (!gs.length) continue;
      const total = gs.reduce((a, g) => a + g.size, 0);
      html += `<div class="sec-head v-${v}"><b>${VERDICT[v][0]}</b><span>${VERDICT[v][1]}</span><span class="sz">${gb(total)}</span></div>`;
      for (const g of gs) {
        const c = cats.find((k) => k.key === g.cat) || { color: '#888', key: 'system' };
        const checkable = g.action !== 'none';
        const st = groupState(g);
        const isOpen = open.has(g.id);
        const count = g.action === 'empty_trash' ? (g.count ? plural(g.count, 'item') : '') : plural(g.count + (g.more || 0), 'item');
        html += `<div class="grp ${v} ${isOpen ? 'open' : ''}" data-g="${g.id}" style="--c:${c.color}">
          <div class="grp-row">
            ${checkable ? `<button class="chk ${st}" data-a="grp">${icon('check')}</button>` : ''}
            <div class="ic">${icon(c.key)}</div>
            <div class="t"><b>${esc(g.title)}</b><span>${esc(g.detail)}</span></div>
            <div class="sz">${gb(g.size)}<small>${count}</small></div>
            ${g.items.length ? `<button class="chev" data-a="open">${icon('chev')}</button>` : '<span style="width:26px"></span>'}
          </div>
          ${isOpen ? `<div class="items">${g.items.map((i) => itemHtml(i, checkable)).join('')}${g.more ? `<div class="more-row">and ${plural(g.more, 'smaller item')}, included when you clear the whole group</div>` : ''}</div>` : ''}
        </div>`;
      }
    }
    el.innerHTML = html;
  }
  $('#clean').addEventListener('click', (e) => {
    const b = e.target.closest('[data-a]');
    if (!b) return;
    const gEl = b.closest('[data-g]');
    const g = gEl && groups.find((x) => x.id === gEl.dataset.g);
    const a = b.dataset.a;
    if (a === 'open' && g) { open.has(g.id) ? open.delete(g.id) : open.add(g.id); renderClean(); return; }
    if (a === 'grp' && g) {
      if (g.action === 'empty_trash') selTrash = !selTrash;
      else { const on = groupState(g) !== 'on'; g.items.forEach((i) => (on ? sel.add(i.path) : sel.delete(i.path))); }
      renderClean(); renderAction(); return;
    }
    itemAction(a, b);
  });
  $('#clean').addEventListener('dblclick', (e) => {
    const row = e.target.closest('.grp-row');
    if (row && !e.target.closest('[data-a]')) row.querySelector('[data-a="open"]') && row.querySelector('[data-a="open"]').click();
  });
  function itemAction(a, b) {
    const path = b.closest('[data-path]') && b.closest('[data-path]').dataset.path;
    if (!path) return;
    if (a === 'item') { sel.has(path) ? sel.delete(path) : sel.add(path); renderClean(); renderLarge(); renderAction(); }
    else if (a === 'reveal') api.reveal(path);
    else if (a === 'explain') {
      if (!claude.has_key) { openSettings('claude'); return; }
      explains[path] = { phase: 'thinking' };
      renderClean(); renderLarge();
      api.explain(path);
    }
  }

  // ---------------------------------------------------------------------------
  // Large files
  // ---------------------------------------------------------------------------
  function renderLarge() {
    const el = $('#large');
    $('#tab-large-n').textContent = large.length ? large.length : '';
    if (!large.length) {
      el.innerHTML = `<div class="empty"><b>${phase === 'ready' ? 'No big files' : 'Measuring'}</b>${phase === 'ready' ? 'Nothing over 50 MB turned up in the folders Dsk can read.' : 'The biggest files show up here when the scan is done.'}</div>`;
      return;
    }
    const list = large.filter((f) => largeFilter === 'all' || (largeFilter === 'gb' && f.size >= 1e9) || (largeFilter === 'old' && f.days >= 90));
    el.innerHTML = `<div class="lf-head"><span>The biggest files Dsk found, biggest first. Nothing is selected for you here.</span><span class="spacer"></span>
      <div class="seg">${[['all', 'All'], ['gb', 'Over 1 GB'], ['old', 'Not opened in 3 months']].map(([k, l]) => `<button data-lf="${k}" class="${largeFilter === k ? 'on' : ''}">${l}</button>`).join('')}</div></div>
      <div class="lf">${list.length ? list.map((f) => {
        const c = cats.find((k) => k.key === f.cat) || { color: '#888' };
        return itemHtml(Object.assign({}, f, { note: `${(cats.find((k) => k.key === f.cat) || {}).label || 'Other'} · opened ${ageText(Date.now() / 1000 - f.days * 86400)}` }), true)
          .replace('<div class="t">', `<span class="dot" style="--c:${c.color}"></span><div class="t">`);
      }).join('') : '<div class="empty">Nothing matches that filter.</div>'}</div>`;
  }
  $('#large').addEventListener('click', (e) => {
    const f = e.target.closest('[data-lf]');
    if (f) { largeFilter = f.dataset.lf; renderLarge(); return; }
    const b = e.target.closest('[data-a]');
    if (b) itemAction(b.dataset.a, b);
  });

  // ---------------------------------------------------------------------------
  // Selection bar and cleaning
  // ---------------------------------------------------------------------------
  function sizeOf(path) {
    for (const g of groups) for (const i of g.items) if (i.path === path) return i.size;
    const f = large.find((x) => x.path === path);
    return f ? f.size : 0;
  }
  let cleanPaths = [];
  function renderAction() {
    const bar_ = $('#action-bar');
    const n = sel.size;
    if (phase === 'cleaning') { bar_.classList.remove('hidden'); return; }
    if (!n && !selTrash) { bar_.classList.add('hidden'); return; }
    bar_.classList.remove('hidden');
    let total = 0; sel.forEach((p) => (total += sizeOf(p)));
    if (selTrash) total += scanState.sizes.trash || 0;
    $('#sel-size').textContent = gb(total);
    $('#sel-what').textContent = [n ? `${plural(n, 'item')} selected` : '', selTrash ? `empty the ${trashName()}` : ''].filter(Boolean).join(' and ');
    const go = $('#sel-go');
    go.querySelector('span').textContent = n ? (settings.use_trash ? `Move to ${trashName()}` : 'Delete') : `Empty ${trashName()}`;
    go.disabled = false;
    $('#clean-progress').classList.add('hidden');
    $('#sel-clear').classList.remove('hidden');
  }
  $('#sel-clear').onclick = () => { sel.clear(); selTrash = false; renderClean(); renderLarge(); renderAction(); };
  $('#sel-go').onclick = () => confirmClean([...sel], selTrash);
  function confirmClean(paths, emptyTrash) {
    if (!paths.length && !emptyTrash) return;
    const byGroup = [];
    groups.forEach((g) => {
      const s = g.items.filter((i) => paths.includes(i.path));
      if (s.length) byGroup.push([g.title, s.length, s.reduce((a, i) => a + i.size, 0)]);
    });
    const inGroups = new Set(groups.flatMap((g) => g.items.map((i) => i.path)));
    const loose = paths.filter((p) => !inGroups.has(p));
    if (loose.length) byGroup.push(['Large files', loose.length, loose.reduce((a, p) => a + sizeOf(p), 0)]);
    if (emptyTrash) byGroup.push([`Empty the ${trashName()}`, 0, scanState.sizes.trash || 0]);
    const total = byGroup.reduce((a, r) => a + r[2], 0);
    const review = paths.some((p) => groups.some((g) => g.verdict !== 'safe' && g.items.some((i) => i.path === p))) || loose.length;
    const lead = paths.length ? (settings.use_trash
      ? `These go to the ${trashName()}, so you can still put anything back. The space comes back when you empty the ${trashName()}.`
      : `These are deleted straight away. You turned off using the ${trashName()} in Settings, so they can’t be put back.`) : '';
    showModal('confirm', `<div class="modal-title"><h2>${paths.length ? (settings.use_trash ? `Move ${gb(total)} to the ${trashName()}?` : `Delete ${gb(total)}?`) : `Empty the ${trashName()}?`}</h2><button class="btn-icon" data-m="close">${icon('x')}</button></div>
      ${lead ? `<p class="lead">${lead}</p>` : ''}
      ${emptyTrash ? `<p class="lead">Emptying the ${trashName()} removes what’s in it for good.</p>` : ''}
      ${review ? `<p class="lead" style="color:var(--warn)">This includes things marked “look first”. Make sure you don’t need them.</p>` : ''}
      <div class="confirm-list">${byGroup.map(([t, n, s]) => `<div><span>${esc(t)}${n ? ` · ${plural(n, 'item')}` : ''}</span><b>${gb(s)}</b></div>`).join('')}</div>
      <div class="foot"><button class="btn-quiet" data-m="close" style="margin-left:auto">Cancel</button>
        <button class="btn-primary inline ${(!settings.use_trash && paths.length) || (emptyTrash && !paths.length) ? 'danger' : ''}" data-m="go">${icon('trash')}${paths.length ? (settings.use_trash ? `Move to ${trashName()}` : 'Delete') + (emptyTrash ? ` and empty` : '') : `Empty ${trashName()}`}</button></div>`,
      async (m) => {
        if (m === 'close') closeModal();
        else if (m === 'go') {
          closeModal();
          const ok = await api.clean(paths, emptyTrash);
          if (ok) { cleanPaths = paths; phase = 'cleaning'; renderAll(); startCleaningBar(); }
        }
      }, 'confirm');
  }
  function startCleaningBar() {
    $('#sel-size').textContent = '';
    $('#sel-what').textContent = settings.use_trash ? `Moving to the ${trashName()}…` : 'Deleting…';
    $('#clean-progress').classList.remove('hidden');
    $('#clean-progress > div').style.width = '0%';
    $('#sel-go').disabled = true;
    $('#sel-clear').classList.add('hidden');
    $('#action-bar').classList.remove('hidden');
  }

  // ---------------------------------------------------------------------------
  // Claude
  // ---------------------------------------------------------------------------
  function renderClaude() {
    const b = $('#ask-claude');
    b.classList.toggle('thinking', claudeState === 'thinking');
    b.disabled = claudeState === 'thinking' || !groups.some((g) => g.action === 'remove');
    b.querySelector('span').textContent = claudeState === 'thinking' ? 'Claude is reviewing…' : Object.keys(advice).length ? 'Ask Claude again' : 'Ask Claude';
    b.title = claude.has_key ? 'Claude reviews each item and says what’s safe to remove' : 'Add your Claude API key in Settings';
  }
  $('#ask-claude').onclick = async () => {
    if (!claude.has_key) { openSettings('claude'); return; }
    claudeState = 'thinking';
    renderClaude();
    await api.ask_claude();
  };
  function showClaudeNote(html, err) {
    const n = $('#claude-note');
    n.innerHTML = `${icon('sparkle')}<div style="flex:1">${err ? `<span class="err">${html}</span>` : html}</div><button class="btn-icon" data-c="close">${icon('x')}</button>`;
    n.classList.remove('hidden');
    n.onclick = (e) => {
      const b = e.target.closest('[data-c]');
      if (!b) return;
      if (b.dataset.c === 'close') n.classList.add('hidden');
      if (b.dataset.c === 'pick') {
        sel.clear();
        Object.entries(advice).forEach(([p, a]) => { if (a.verdict === 'safe') sel.add(p); });
        renderClean(); renderAction();
      }
    };
  }

  // ---------------------------------------------------------------------------
  // Modals, toasts, settings
  // ---------------------------------------------------------------------------
  function toast(text, err, action) {
    const t = document.createElement('div');
    t.className = 'toast' + (err ? ' err' : '');
    t.innerHTML = icon(err ? 'alert' : 'check') + `<span>${esc(text)}</span>`;
    if (action) {
      const b = document.createElement('button');
      b.textContent = action.label;
      b.onclick = () => { action.run(); t.remove(); };
      t.appendChild(b);
    }
    $('#toasts').appendChild(t);
    setTimeout(() => { t.style.transition = 'opacity .3s'; t.style.opacity = 0; setTimeout(() => t.remove(), 300); }, action ? 8000 : 4200);
  }
  function closeModal() { $('#modal-root').innerHTML = ''; modal = null; }
  function showModal(name, html, onClick, cls) {
    const box = modal === name && $('#modal-root .modal');
    modal = name;
    if (box) { box.className = `modal ${cls || ''}`; box.innerHTML = html; }
    else $('#modal-root').innerHTML = `<div class="modal-back"><div class="modal ${cls || ''}">${html}</div></div>`;
    $('#modal-root .modal-back').onclick = (e) => {
      if (e.target.classList.contains('modal-back')) return closeModal();
      const el = e.target.closest('[data-m]');
      if (el) onClick(el.dataset.m, el);
    };
  }
  const sw = (on) => `<span class="switch ${on ? 'on' : ''}"></span>`;
  const opt = (key, title, detail) => `<button class="opt" data-m="toggle" data-key="${key}"><div class="t"><b>${title}</b><span>${detail}</span></div>${sw(settings[key])}</button>`;
  const ago = (iso) => {
    if (!iso) return 'Never checked';
    const s = (Date.now() - new Date(iso).getTime()) / 1000;
    if (s < 60) return 'Checked just now';
    if (s < 3600) return `Checked ${Math.round(s / 60)} min ago`;
    if (s < 86400) return `Checked ${Math.round(s / 3600)} h ago`;
    return 'Checked ' + new Date(iso).toLocaleDateString();
  };
  function updateLine() {
    if (!upd) return ['', ''];
    switch (upd.phase) {
      case 'checking': return ['Checking for updates…', ''];
      case 'uptodate': return ["You're up to date", 'ok'];
      case 'available': return [`Version ${upd.latest} is available`, 'ok'];
      case 'downloading': return [upd.progress >= 1 ? `Preparing ${upd.latest}…` : `Downloading ${upd.latest}… ${Math.round(upd.progress * 100)}%`, ''];
      case 'ready': return [`Version ${upd.latest} is ready to install`, 'ok'];
      case 'installing': return ['Installing…', ''];
      case 'failed': return [upd.error || 'Update failed', 'bad'];
      default: return [ago(upd.last_checked), ''];
    }
  }
  function renderUpdateRow() {
    const el = $('#upd-row');
    if (!el) return;
    const [line, cls] = updateLine();
    const has = upd && ['available', 'downloading', 'ready'].includes(upd.phase);
    el.innerHTML = `<div class="t"><b>Dsk ${esc(upd ? upd.current : '')}</b><span class="${cls}">${esc(line)}</span></div>
      ${has ? `<button class="btn-quiet" data-m="see-update">${icon('download')}See update</button>` : `<button class="btn-quiet" data-m="check" ${upd && upd.phase === 'checking' ? 'disabled' : ''}>${icon('refresh')}Check now</button>`}`;
  }
  function wizGroup() {
    if (!isWin()) return '';
    return `<div class="label">WizTree</div><div class="group">
      ${opt('wiztree', 'Scan with WizTree when it’s installed', 'WizTree reads the drive’s file table directly, so a full scan takes seconds')}
      <div class="ver-row"><div class="t"><b>${wiz && wiz.found ? 'Found' : 'Not found'}</b><span>${wiz && wiz.found ? esc(wiz.found) : 'Install WizTree, or point Dsk at WizTree64.exe'}</span></div>
        ${wiz && wiz.found ? '' : '<button class="btn-quiet" data-m="wiz-get">Get WizTree</button>'}<button class="btn-quiet" data-m="wiz-pick">Choose…</button></div>
      ${opt('wiztree_admin', 'Let WizTree ask for admin rights', 'Needed for its fastest mode. Without it, WizTree scans more slowly.')}
    </div>`;
  }
  function openSettings(focus) {
    showModal('settings', `
      <div class="modal-title"><h2>Settings</h2><button class="btn-icon" data-m="close">${icon('x')}</button></div>
      <div class="label">Removing</div>
      <div class="group">
        ${opt('use_trash', `Move to the ${trashName()} first`, `Everything Dsk removes goes to the ${trashName()}, so you can put it back. Turn off to delete straight away.`)}
        ${platform === 'darwin' ? `<div class="ver-row"><div class="t"><b>Full Disk Access</b><span>Lets Dsk measure the Trash, Mail and other protected folders. Add Dsk in Privacy & Security.</span></div><button class="btn-quiet" data-m="privacy">Open</button></div>` : ''}
      </div>
      ${wizGroup()}
      <div class="label">Claude</div>
      <div class="group" id="claude-group"></div>
      <div class="label">Updates</div>
      <div class="group">
        <div class="ver-row" id="upd-row"></div>
        ${opt('auto_check', 'Check for updates automatically', 'Looks for a new version at launch and every few hours')}
        ${opt('auto_install', 'Download and install updates automatically', 'Downloads in the background and installs when you quit')}
      </div>
      <div class="label">About</div>
      <div class="about">Dsk measures your disk on this computer and never uploads your files. It only removes what you choose, and by default sends it to the ${trashName()}. If you ask Claude, the list of paths, sizes and dates (not the files) goes to Claude with your own API key.</div>
      <div class="foot"><button class="link" data-m="page">Release notes on GitHub</button><button class="link" data-m="welcome" style="margin-right:0">Show welcome screen</button></div>`,
      async (m, el) => {
        if (m === 'close') closeModal();
        else if (m === 'toggle') {
          const k = el.dataset.key;
          settings = await api.set_setting(k, !settings[k]);
          el.querySelector('.switch').classList.toggle('on', !!settings[k]);
          renderAction();
        } else if (m === 'check') { upd = await api.check_updates(); renderUpdateRow(); renderPill(); }
        else if (m === 'see-update') openUpdate();
        else if (m === 'page') api.open_url(upd ? upd.page : '');
        else if (m === 'welcome') { closeModal(); showWelcome(); }
        else if (m === 'key-save' || m === 'key-remove') await saveKey(m === 'key-remove');
        else if (m === 'console') api.open_url('https://console.anthropic.com/settings/keys');
        else if (m === 'privacy') api.open_privacy();
        else if (m === 'wiz-get') api.open_url('https://diskanalyzer.com/download');
        else if (m === 'wiz-pick') { wiz = await api.pick_wiztree(); openSettings(); }
      }, 'settings');
    renderUpdateRow();
    renderClaudeGroup();
    if (focus === 'claude') { const k = $('#key-input'); if (k) { k.scrollIntoView({ block: 'center' }); k.focus(); } }
  }
  function renderClaudeGroup() {
    const g = $('#claude-group');
    if (!g) return;
    g.innerHTML = `<div class="ver-row"><div class="t"><b>API key</b><span class="${claude.has_key ? 'ok' : ''}">${claude.has_key
      ? (claude.env ? 'Using ANTHROPIC_API_KEY from the environment' : `Saved in your ${isWin() ? 'Windows Credential Manager' : 'Keychain'} ${esc(claude.hint)}`)
      : 'Not set. Add one to let Claude review what to remove.'}</span></div>
      ${claude.has_key && !claude.env ? `<button class="btn-quiet" data-m="key-remove">${icon('trash')}Remove</button>` : ''}</div>
      <div><div class="key-row" style="flex:1"><input id="key-input" type="password" placeholder="${claude.has_key ? 'Paste a new key to replace it' : 'sk-ant-…'}" autocomplete="off" spellcheck="false">
      <button class="btn-quiet" data-m="key-save">Save</button></div></div>
      <div><span class="hint">Your key stays on this computer. A review sends paths, sizes and dates, never file contents, and costs a few cents. <button class="link" data-m="console">Get a key</button></span></div>`;
    const inp = $('#key-input');
    if (inp) inp.onkeydown = (e) => { if (e.key === 'Enter') saveKey(false); };
  }
  async function saveKey(remove) {
    const inp = $('#key-input');
    const v = remove ? '' : (inp ? inp.value.trim() : '');
    if (!remove && !v) return;
    claude = await api.set_claude_key(v);
    if (claude.error) toast(claude.error, true);
    else toast(remove ? 'API key removed' : 'API key saved');
    renderClaudeGroup();
    renderClaude();
  }
  function renderPill() {
    const p = $('#update-pill');
    if (!upd || !['available', 'downloading', 'ready', 'installing'].includes(upd.phase)) { p.classList.add('hidden'); return; }
    p.classList.remove('hidden');
    p.innerHTML = upd.phase === 'ready' ? `${icon('refresh')}Restart to update` :
      upd.phase === 'downloading' ? (upd.progress >= 1 ? `${icon('refresh')}Preparing update…` : `${icon('download')}Updating ${Math.round(upd.progress * 100)}%`) :
      upd.phase === 'installing' ? `${icon('refresh')}Installing…` : `${icon('download')}Update to ${esc(upd.latest)}`;
  }
  function patchUpdateProgress() {
    const b = $('#modal-root .progress > div');
    const line = $('#modal-root .update-hero p');
    if (!b || !line) return false;
    const pct = Math.round((upd.progress || 0) * 100);
    b.style.width = pct + '%';
    line.textContent = pct >= 100 ? 'Checking and unpacking the update…' : `Downloading… ${pct}%`;
    return true;
  }
  const logo = (size) => `<span class="mark" style="--size:${size}px">dsk<span class="dots" aria-hidden="true">${'<i></i>'.repeat(7)}</span></span>`;
  function openUpdate() {
    if (!upd) return;
    const ph = upd.phase;
    const pct = Math.round((upd.progress || 0) * 100);
    const sub = ph === 'ready' ? 'Downloaded and ready. Restart now, or it installs the next time you quit.' :
      ph === 'downloading' ? (pct >= 100 ? 'Checking and unpacking the update…' : `Downloading… ${pct}%`) : ph === 'installing' ? 'Installing and restarting…' :
      ph === 'failed' ? (upd.error || 'Something went wrong.') : ph === 'uptodate' ? "You're on the newest version." :
      `You have ${esc(upd.current)}.` + (upd.can_install ? '' : ' This copy runs from source, so the download page opens instead.');
    const primary = ph === 'ready' ? `<button class="btn-primary inline" data-m="install">${icon('refresh')}Restart to update</button>` :
      ph === 'available' || ph === 'failed' ? `<button class="btn-primary inline" data-m="${upd.can_install ? 'download' : 'page'}">${icon('download')}${upd.can_install ? 'Download update' : 'Open download page'}</button>` : '';
    showModal('update', `
      <div class="update-hero">
        <div class="logomark lg">${logo(28)}</div>
        <div><h2>${upd.latest ? 'Dsk ' + esc(upd.latest) : 'Updates'}</h2><p class="${ph === 'failed' ? 'err' : ''}">${sub}</p></div>
      </div>
      ${ph === 'downloading' ? `<div class="progress"><div style="width:${pct}%"></div></div>` : ''}
      ${upd.notes ? `<div class="label">What's new</div><div class="notes">${esc(upd.notes)}</div>` : ''}
      <div class="foot"><button class="link" data-m="page">View on GitHub</button><button class="btn-quiet" data-m="close">Later</button>${primary}</div>`,
      (m) => {
        if (m === 'close') closeModal();
        else if (m === 'install') api.install_update();
        else if (m === 'download') api.download_update();
        else if (m === 'page') api.open_url(upd.page);
      });
  }
  function showWelcome() {
    const w = $('#welcome');
    let page = 0;
    const pages = [
      () => `<div class="logomark lg" style="width:96px;height:96px;border-radius:26px">${logo(36)}</div>
        <h1>Welcome to Dsk</h1>
        <p class="lead">See what’s filling your disk, clear what’s safe in one go,<br>and look before you remove anything that matters.</p>
        <div class="facts">
          <div class="card fact">${icon('trash')}<b>${trashName()} first</b><span>Everything Dsk removes goes to the ${trashName()}, so you can put it back.</span></div>
          <div class="card fact">${icon('shield')}<b>Careful by default</b><span>Only rebuildable things are ticked. Your files are never ticked for you.</span></div>
          <div class="card fact">${icon('sparkle')}<b>Ask Claude</b><span>Optional second opinion on what’s safe, with your own API key.</span></div>
        </div>`,
      () => `<h1>Stay up to date</h1>
        <p class="lead">New versions arrive from GitHub with more things Dsk knows how to clear.</p>
        <div class="group">
          ${opt('auto_check', 'Check for updates automatically', 'Looks for a new version at launch and every few hours')}
          ${opt('auto_install', 'Download and install updates automatically', 'Downloads in the background and installs when you quit')}
        </div>`,
    ];
    const render = () => {
      w.innerHTML = `<div class="glow"></div><div class="dots">${pages.map((_, i) => `<i class="${i <= page ? 'on' : ''} ${i === page ? 'cur' : ''}"></i>`).join('')}</div>
        <div class="page">${pages[page]()}</div>
        <div class="foot">${page ? '<button class="btn-quiet" data-w="back">Back</button>' : ''}
          <button class="btn-primary" data-w="next">${page === pages.length - 1 ? 'Get started' : 'Continue'}</button></div>`;
    };
    w.onclick = async (e) => {
      const t = e.target.closest('[data-w],[data-m]');
      if (!t) return;
      if (t.dataset.m === 'toggle') {
        const k = t.dataset.key;
        settings = await api.set_setting(k, !settings[k]);
        t.querySelector('.switch').classList.toggle('on', !!settings[k]);
      } else if (t.dataset.w === 'back') { page--; render(); }
      else if (t.dataset.w === 'next') {
        if (page < pages.length - 1) { page++; render(); }
        else { w.classList.add('hidden'); settings = await api.set_setting('welcomed', true); }
      }
    };
    render();
    w.classList.remove('hidden');
  }

  function renderAll() {
    renderHead(); renderCats(); renderFoot(); renderClean(); renderLarge(); renderAction(); renderClaude();
    const safeN = groups.filter((g) => g.verdict !== 'keep').length;
    $('#tab-clean-n').textContent = safeN ? safeN : '';
  }
  $('#tabs').addEventListener('click', (e) => {
    const t = e.target.closest('[data-tab]');
    if (!t) return;
    tab = t.dataset.tab;
    document.querySelectorAll('.tab').forEach((b) => b.classList.toggle('on', b === t));
    $('#clean').classList.toggle('hidden', tab !== 'clean');
    $('#large').classList.toggle('hidden', tab !== 'large');
  });
  $('#rescan').onclick = async () => { if (await api.scan()) { phase = 'scanning'; groups = []; large = []; sel.clear(); selTrash = false; advice = {}; $('#claude-note').classList.add('hidden'); renderAll(); } };
  $('#open-settings').onclick = () => openSettings();
  $('#update-pill').onclick = () => openUpdate();
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });
  window.addEventListener('resize', () => sizeBar());

  // ---------------------------------------------------------------------------
  // Events from Python
  // ---------------------------------------------------------------------------
  window.App = {
    on(event, p) {
      if (event === 'scan') {
        scanState = Object.assign({}, scanState, p);
        if (phase !== 'cleaning') phase = p.done ? (phase === 'ready' ? 'ready' : 'looking') : 'scanning';
        renderHead(); renderCats();
        if (phase !== 'ready') renderFoot();
      } else if (event === 'looking') { phase = 'looking'; renderHead(); renderFoot(); }
      else if (event === 'groups') {
        const first = !groups.length;
        groups = p.groups || []; summary = p.summary || summary; advice = p.advice || {};
        if (phase !== 'cleaning') phase = 'ready';
        if (first) groups.forEach((g) => { if (g.verdict === 'safe' && g.action === 'remove') g.items.forEach((i) => sel.add(i.path)); });
        // drop selections that no longer exist
        const live = new Set(groups.flatMap((g) => g.items.map((i) => i.path)).concat(large.map((f) => f.path)));
        [...sel].forEach((s) => { if (!live.has(s)) sel.delete(s); });
        if (!groups.some((g) => g.action === 'empty_trash')) selTrash = false;
        renderAll();
      } else if (event === 'large') { large = p || []; renderLarge(); }
      else if (event === 'cleaning') { phase = 'cleaning'; renderHead(); renderFoot(); }
      else if (event === 'clean-progress') {
        $('#clean-progress > div').style.width = (100 * p.done / Math.max(1, p.total)) + '%';
        scanState.current = p.current; renderHead();
      } else if (event === 'cleaned') {
        burst(p.moved);
        if (p.emptied) burst({ trash: p.emptied });
        phase = 'ready';
        cleanPaths.forEach((x) => sel.delete(x)); cleanPaths = [];
        if (p.emptied || p.trash_error) selTrash = false;
        const parts = [];
        if (p.done) parts.push(p.to_trash ? `Moved ${gb(p.freed)} to the ${trashName()}` : `Freed ${gb(p.freed)}`);
        if (p.emptied) parts.push(`emptied the ${trashName()} (${gb(p.emptied)})`);
        if (p.failed_count) parts.push(`${p.failed_count} skipped (in use or not allowed)`);
        if (p.trash_error) parts.push(p.trash_error);
        if (parts.length) toast(parts.join(', '), !!(p.failed_count || p.trash_error),
          p.to_trash && p.done && !p.emptied ? { label: `Empty ${trashName()}`, run: () => confirmClean([], true) } : null);
        renderAll();
      } else if (event === 'claude') {
        claudeState = p.phase;
        if (p.phase === 'done') {
          const n = Object.values(advice).filter((a) => a.verdict === 'safe').length;
          showClaudeNote(`${esc(p.summary)}${n ? ` <button class="link" data-c="pick" style="color:#f0a487;margin-left:6px">Select the ${plural(n, 'item')} Claude says are safe</button>` : ''}`);
        } else if (p.phase === 'failed') { showClaudeNote(esc(p.error), true); }
        renderClaude();
      } else if (event === 'explain') { explains[p.path] = p; renderClean(); renderLarge(); }
      else if (event === 'toast') toast(p.text, p.err);
      else if (event === 'update') {
        const prev = upd && upd.phase;
        upd = p;
        renderPill();
        if (modal === 'update' && !(prev === 'downloading' && p.phase === 'downloading' && patchUpdateProgress())) openUpdate();
        else if (modal === 'settings') renderUpdateRow();
        if (prev !== 'ready' && p.phase === 'ready' && modal !== 'update')
          toast(`Version ${p.latest} is ready`, false, { label: 'Restart', run: () => api.install_update() });
      }
    },
  };

  // ---------------------------------------------------------------------------
  // Start
  // ---------------------------------------------------------------------------
  async function start(a) {
    api = a;
    const info = await api.info();
    platform = info.platform || 'darwin';
    document.body.classList.add(platform === 'darwin' ? 'mac' : platform.startsWith('win') ? 'win' : 'other');
    $('#version').textContent = 'v' + info.version;
    settings = info.settings || {};
    upd = info.update; claude = info.claude || claude; cats = info.categories || []; wiz = info.wiztree;
    scanState.disk = info.disk || scanState.disk;
    cats.forEach((c) => { bar.shown[c.key] = 0; scanState.sizes[c.key] = 0; });
    renderPill();
    renderAll();
    setTimeout(() => { $('#splash').classList.add('out'); $('#app').classList.add('in'); sizeBar(); requestAnimationFrame(drawBar); }, 1400);
    setTimeout(() => $('#splash').remove(), 2050);
    setTimeout(async () => { if (await api.scan()) { phase = 'scanning'; renderAll(); } }, 1500);
    if (!settings.welcomed) setTimeout(showWelcome, 1700);
  }

  // Demo data for previewing the UI in a plain browser (open index.html?demo).
  function demoApi() {
    const G = 1e9;
    const target = { apps: 52.6 * G, dev: 36.3 * G, photos: 58.5 * G, movies: 43.1 * G, docs: 39.5 * G, music: 12 * G, system: 29.8 * G, caches: 42.1 * G, trash: 0 };
    if (location.search.includes('trash')) target.trash = 31.4 * G;
    const it = (name, show, size, d, note) => ({ path: '/Users/demo/' + show.slice(2), show, name, size, mtime: Date.now() / 1000 - d * 86400, note });
    const demoGroups = [
      { id: 'app-caches', title: 'App caches', detail: 'Temporary files apps keep to load faster. They rebuild them when needed, so an app may open a little slower the first time.', verdict: 'safe', cat: 'caches', action: 'remove',
        items: [it('com.apple.Safari', '~/Library/Caches/com.apple.Safari', 3.1 * G, 1), it('com.spotify.client', '~/Library/Caches/com.spotify.client', 6.4 * G, 2), it('Homebrew', '~/Library/Caches/Homebrew', 4.2 * G, 5), it('com.penrose.studio', '~/Library/Caches/com.penrose.studio', 9.8 * G, 3), it('Google', '~/Library/Caches/Google', 2.2 * G, 0)] },
      { id: 'xcode-derived', title: 'Xcode build files', detail: 'Intermediate build output. Xcode makes it again on the next build.', verdict: 'safe', cat: 'dev', action: 'remove',
        items: [it('Pin-abcd', '~/Library/Developer/Xcode/DerivedData/Pin-abcd', 7.9 * G, 12), it('Dwn-efgh', '~/Library/Developer/Xcode/DerivedData/Dwn-efgh', 3.3 * G, 30)] },
      { id: 'dev-caches', title: 'Package manager caches', detail: 'Downloaded copies of packages (npm, cargo, Gradle, pnpm, pip). They’re fetched again when a project needs them.', verdict: 'safe', cat: 'dev', action: 'remove',
        items: [it('_cacache', '~/.npm/_cacache', 4.6 * G, 1), it('caches', '~/.gradle/caches', 2.1 * G, 40)] },
      { id: 'logs', title: 'Logs', detail: 'Diagnostic logs apps write as they run. Nothing reads them unless you’re troubleshooting.', verdict: 'safe', cat: 'caches', action: 'remove', items: [it('DiagnosticReports', '~/Library/Logs/DiagnosticReports', 0.6 * G, 3)] },
      { id: 'stale-deps', title: 'Project dependencies you haven’t touched in a month', detail: 'node_modules, virtual environments and build folders in projects untouched for 30+ days. npm install brings them back.', verdict: 'review', cat: 'dev', action: 'remove',
        items: [it('node_modules', '~/Documents/old-portfolio/node_modules', 1.4 * G, 210, 'node_modules · project untouched for 210 days'), it('.venv', '~/Documents/ml-test/.venv', 2.9 * G, 95, '.venv · project untouched for 95 days')] },
      { id: 'installers', title: 'Installers in Downloads', detail: 'Disk images, packages and zips more than a week old. Once an app is installed, its installer isn’t needed.', verdict: 'review', cat: 'docs', action: 'remove',
        items: [it('DaVinci_Resolve_19.dmg', '~/Downloads/DaVinci_Resolve_19.dmg', 4.1 * G, 60), it('Xcode_16.xip', '~/Downloads/Xcode_16.xip', 3.4 * G, 120)] },
      { id: 'device-support', title: 'iPhone debug symbols', detail: 'Xcode copies these from each iPhone or iPad you plug in. Old iOS versions are dead weight.', verdict: 'review', cat: 'dev', action: 'remove', items: [it('17.4 (21E219)', '~/Library/Developer/Xcode/iOS DeviceSupport/17.4 (21E219)', 4.8 * G, 200)] },
      { id: 'trash', title: 'Trash', detail: 'Things you’ve already deleted. Emptying the Trash removes them for good.', verdict: 'safe', cat: 'trash', action: 'empty_trash', items: [], count: 214 },
      { id: 'keep-photos', title: 'Photos library', detail: 'Your photo library. Manage it in Photos: turn on Optimise Mac Storage to keep full-size originals only in iCloud.', verdict: 'keep', cat: 'photos', action: 'none', items: [it('Photos Library.photoslibrary', '~/Pictures/Photos Library.photoslibrary', 51.2 * G, 0)] },
      { id: 'keep-system', title: 'macOS and system data', detail: 'macOS itself, its snapshots, swap and other system files. macOS manages these.', verdict: 'keep', cat: 'system', action: 'none', items: [] },
    ];
    demoGroups.forEach((g) => { if (!g.count) g.count = g.items.length; if (g.id === 'trash') g.size = target.trash; else if (g.id === 'keep-system') g.size = target.system; else g.size = g.items.reduce((a, i) => a + i.size, 0); });
    const shownGroups = demoGroups.filter((g) => g.size > 0);
    const paths = ['~/Applications/Figma.app', '~/Library/Developer/Xcode', '~/Pictures/Photos Library.photoslibrary/resources', '~/Movies/Final Cut/Render Files', '~/Documents/Projects', '~/Music/Logic', '~/Library/Caches/com.penrose.studio'];
    const keys = Object.keys(target);
    const sum = (g) => ({ safe: g.filter((x) => x.verdict === 'safe').reduce((a, x) => a + x.size, 0), review: g.filter((x) => x.verdict === 'review').reduce((a, x) => a + x.size, 0) });
    const largeList = [
      { path: '/Users/demo/Movies/wedding-raw.mov', show: '~/Movies/wedding-raw.mov', name: 'wedding-raw.mov', size: 14.2 * G, mtime: 0, cat: 'movies', days: 140 },
      { path: '/Users/demo/Downloads/DaVinci_Resolve_19.dmg', show: '~/Downloads/DaVinci_Resolve_19.dmg', name: 'DaVinci_Resolve_19.dmg', size: 4.1 * G, mtime: 0, cat: 'docs', days: 60 },
      { path: '/Users/demo/Documents/Parallels/Windows 11.pvm', show: '~/Documents/Parallels/Windows 11.pvm', name: 'Windows 11.pvm', size: 38.5 * G, mtime: 0, cat: 'docs', days: 20 },
      { path: '/Users/demo/Music/Samples.zip', show: '~/Music/Samples.zip', name: 'Samples.zip', size: 2.3 * G, mtime: 0, cat: 'music', days: 400 },
    ].sort((a, b) => b.size - a.size);
    const stopAt = location.search.includes('scanning') ? 0.62 : 1;
    return {
      info: async () => ({ version: '1.0.0', platform: location.search.includes('win') ? 'win32' : 'darwin', home: '/Users/demo',
        settings: { use_trash: true, wiztree: true, wiztree_admin: true, auto_check: true, auto_install: true, welcomed: !location.search.includes('welcome') },
        update: { phase: 'uptodate', current: '1.0.0', latest: '1.0.0', progress: 0, can_install: true, page: 'https://github.com', last_checked: new Date().toISOString() },
        claude: { has_key: true, hint: '…3f9a' }, wiztree: { found: null },
        categories: [['apps', 'Apps', '#3d8bff'], ['dev', 'Developer', '#2fd36b'], ['photos', 'Photos', '#ff4fa3'], ['movies', 'Movies', '#a46bff'], ['docs', 'Documents', '#22d3ee'], ['music', 'Music', '#facc15'], ['system', 'System data', '#a1a1aa'], ['caches', 'Caches', '#ff8a3d'], ['trash', 'Trash', '#ff5b5b']].map(([key, label, color]) => ({ key, label, color })),
        disk: { total: 512 * G, used: 313.9 * G + target.trash, free: 198.1 * G } }),
      scan: async () => {
        let f = 0;
        const tick = () => {
          f = Math.min(stopAt, f + 0.035);
          const sizes = {};
          keys.forEach((k, i) => { sizes[k] = k === 'system' ? (f >= 1 ? target[k] : 0) : target[k] * Math.min(1, Math.max(0, f * 1.4 - i * 0.04)); });
          App.on('scan', { disk: { total: 512 * G, used: 313.9 * G + target.trash, free: 198.1 * G }, sizes, done: f >= 1, current: paths[Math.floor(f * 6.9) % paths.length], seconds: 11.8, engine: 'walk', denied_count: 0 });
          if (f < stopAt) setTimeout(tick, 90);
          else if (f >= 1) {
            App.on('looking', {});
            setTimeout(() => {
              App.on('groups', { groups: shownGroups, summary: sum(shownGroups), advice: {} });
              App.on('large', largeList);
              if (location.search.includes('claude')) setTimeout(() => { document.querySelector('#ask-claude').click(); }, 300);
            }, 900);
          }
        };
        tick();
        return true;
      },
      set_setting: async (k, v) => { settings[k] = v; return Object.assign({}, settings); },
      set_claude_key: async (k) => ({ has_key: !!k, hint: k ? '…' + k.slice(-4) : '' }),
      check_updates: async () => upd, download_update() {}, install_update() {}, open_url() {}, reveal() {}, open_privacy() {}, pick_wiztree: async () => wiz,
      clean: async (ps, emptyT) => {
        setTimeout(() => {
          const moved = {};
          shownGroups.forEach((g) => g.items.forEach((i) => { if (ps.includes(i.path)) moved[g.cat] = (moved[g.cat] || 0) + i.size; }));
          const freed = Object.values(moved).reduce((a, b) => a + b, 0);
          Object.entries(moved).forEach(([k, v]) => { target[k] -= v; target.trash += v; });
          shownGroups.forEach((g) => { g.items = g.items.filter((i) => !ps.includes(i.path)); if (g.action === 'remove') { g.size = g.items.reduce((a, i) => a + i.size, 0); g.count = g.items.length; } });
          App.on('cleaned', { done: ps.length, failed: [], failed_count: 0, freed, moved, to_trash: true, emptied: 0 });
          App.on('scan', { sizes: Object.assign({}, target), done: true });
          const live = shownGroups.filter((g) => g.size > 0 || g.action === 'none');
          App.on('groups', { groups: live, summary: sum(live), advice: {} });
        }, 900);
        return true;
      },
      ask_claude: async () => {
        setTimeout(() => {
          const adv = {};
          shownGroups.forEach((g) => g.items.forEach((i) => { adv[i.path] = g.verdict === 'safe' ? { verdict: 'safe', reason: 'Rebuilt automatically; removing it only costs a slower first launch.' } : { verdict: 'review', reason: 'Fine to remove if you no longer work on this project.' }; }));
          App.on('groups', { groups: shownGroups, summary: sum(shownGroups), advice: adv });
          App.on('claude', { phase: 'done', summary: 'Start with the Penrose Studio cache and Xcode build files: 17.7 GB that rebuilds itself. The old DaVinci installer is safe once Resolve is installed.' });
          if (location.search.includes('open')) { document.querySelector('[data-g="app-caches"] [data-a="open"]').click(); }
        }, 1200);
        return true;
      },
      explain: (p) => setTimeout(() => App.on('explain', { path: p, phase: 'done', what: 'Cache for Penrose Studio.', verdict: 'safe', reason: 'The app rebuilds it on launch.', how: '' }), 900),
    };
  }

  if (!location.search.includes('demo')) {
    let started = false;
    const reveal = (msg) => {
      const s = $('#splash');
      if (!s || s.classList.contains('out')) return;
      s.classList.add('out'); $('#app').classList.add('in');
      if (msg) toast(msg, true);
    };
    const boot = () => {
      const a = window.pywebview && window.pywebview.api;
      if (started || !a || typeof a.info !== 'function') return;
      started = true;
      start(a).catch((e) => reveal("Dsk couldn't start: " + ((e && e.message) || e)));
    };
    window.addEventListener('pywebviewready', boot);
    boot();
    setTimeout(() => reveal(started ? '' : "Dsk's engine didn't answer. Quit Dsk and open it again."), 15000);
  } else {
    start(demoApi());
  }
})();
