// Schematrix editor. Geometry comes from the Python symbol library over /api/geometry; everything else is local.
import * as G from './geom.js';

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const NS = 'http://www.w3.org/2000/svg';
const clone = (o) => JSON.parse(JSON.stringify(o));
const snapTo = (v, g) => Math.round(v / g) * g;

// ---------------------------------------------------------------- api
const api = {
  async req(method, url, body, raw) {
    const r = await fetch(url, { method, headers: body !== undefined && !raw ? { 'Content-Type': 'application/json' } : {},
      body: body === undefined ? undefined : raw ? body : JSON.stringify(body) });
    if (!r.ok) {
      let msg = r.statusText;
      try { msg = (await r.json()).detail || msg; } catch { /* not json */ }
      throw new Error(msg);
    }
    return r;
  },
  get: (u) => api.req('GET', u).then((r) => r.json()),
  post: (u, b) => api.req('POST', u, b).then((r) => r.json()),
  blob: (u, b) => api.req('POST', u, b).then((r) => r.blob()),
  put: (u, text) => api.req('PUT', u, text, true).then((r) => r.json()),
  del: (u) => api.req('DELETE', u).then((r) => r.json()),
};

// ---------------------------------------------------------------- state
const S = {
  info: {}, cat: {}, catList: [], geo: new Map(), geoQueue: new Map(), geoTimer: 0,
  tabs: [], cur: null, tool: 'select', placing: null, draft: null, drag: null, style: '',
  mouse: [0, 0], space: false, grid: true, lastFlag: 'NET', wireMode: 'auto', rawBB: new Map(), netHL: null,
};
const T = () => S.cur;
const D = () => S.cur.doc;

function newDoc(title = 'Untitled') {
  return { version: 1, meta: { title, description: '' }, page: { width: 800, height: 500, auto: false, margin: 20, grid: 5, junctions: true },
    theme: 'instrix', elements: [] };
}

// ---------------------------------------------------------------- geometry cache
function geoKey(sym, props) {
  const c = S.cat[sym];
  if (!c) return sym;
  return sym + '|' + c.geom_keys.map((k) => String(props?.[k] ?? c.props[k].default)).join('|');
}
function geoOf(e) {
  const k = geoKey(e.sym, e.props);
  const g = S.geo.get(k);
  if (g) return g;
  if (!S.geoQueue.has(k)) {
    const c = S.cat[e.sym];
    const props = {};
    if (c) for (const gk of c.geom_keys) if (e.props && gk in e.props) props[gk] = e.props[gk];
    S.geoQueue.set(k, { sym: e.sym, props });
    clearTimeout(S.geoTimer);
    S.geoTimer = setTimeout(flushGeo, 15);
  }
  return null;
}
async function flushGeo() {
  const items = [...S.geoQueue];
  if (!items.length) return;
  S.geoQueue.clear();
  try {
    const res = await api.post('/api/geometry', { items: items.map(([, v]) => v) });
    res.forEach((g, i) => { if (!g.error) S.geo.set(items[i][0], g); else toast(g.error, true); });
  } catch (err) { toast('geometry: ' + err.message, true); }
  render();
  if (S.cur?.fitPending) fit();
}
const pinsOf = (e) => G.compPins(e, geoOf(e));

// ---------------------------------------------------------------- tabs & history
let tabSeq = 0;
function openTab(doc, path = null, focus = true) {
  const t = { id: ++tabSeq, doc, path, undo: [], redo: [], dirty: false, sel: new Set(), view: null };
  // replace the blank start-up tab instead of piling up "Untitled"s
  const blank = S.tabs.find((o) => !o.path && !o.dirty && !o.doc.elements.length && !o.undo.length);
  if (blank && doc.elements.length) S.tabs.splice(S.tabs.indexOf(blank), 1);
  S.tabs.push(t);
  if (focus) switchTab(t);
  return t;
}
function switchTab(t) {
  S.cur = t; S.draft = null; S.netHL = null; S.rawBB.clear();
  render(); renderTabs(); renderInspector();
  if (!t.view) { t.fitPending = true; requestAnimationFrame(() => fit()); } else applyView();
}
async function closeTab(t) {
  if (t.dirty && !(await confirmBox(`“${tabTitle(t)}” has unsaved changes. Close it anyway?`, 'Close'))) return;
  const i = S.tabs.indexOf(t);
  S.tabs.splice(i, 1);
  if (!S.tabs.length) openTab(newDoc());
  else if (S.cur === t) switchTab(S.tabs[Math.max(0, i - 1)]);
  renderTabs(); persist();
}
const tabTitle = (t) => t.doc.meta?.title || (t.path ? t.path.replace(/\.json$/, '') : 'Untitled');
function renderTabs() {
  const el = $('#tabs');
  el.innerHTML = '';
  for (const t of S.tabs) {
    const d = document.createElement('div');
    d.className = 'tab' + (t === S.cur ? ' on' : '');
    d.title = t.path || 'not saved yet';
    d.innerHTML = `<span>${G.esc(tabTitle(t))}</span>${t.dirty ? '<i class="d"></i>' : ''}<button title="Close">×</button>`;
    d.onclick = (ev) => { if (ev.target.tagName === 'BUTTON') closeTab(t); else if (t !== S.cur) switchTab(t); };
    d.onauxclick = (ev) => { if (ev.button === 1) closeTab(t); };
    el.append(d);
  }
  const nb = document.createElement('button');
  nb.className = 'newtab'; nb.textContent = '+'; nb.title = 'New schematic (Ctrl+N)';
  nb.onclick = () => cmd('new');
  el.append(nb);
  $('#savebtn').classList.toggle('dirty', !!S.cur?.dirty);
  document.title = (S.cur?.dirty ? '• ' : '') + (S.cur ? tabTitle(S.cur) + ' — ' : '') + 'Schematrix';
}

function snapshot() { return JSON.stringify(D()); }
function pushUndo(snap, coalesce) {
  const t = T(), now = Date.now();
  if (coalesce && t.lastCo === coalesce && now - t.lastCoT < 1500) { t.lastCoT = now; return; }
  t.undo.push(snap);
  if (t.undo.length > 300) t.undo.shift();
  t.redo = []; t.lastCo = coalesce; t.lastCoT = now;
}
function changed() {
  T().dirty = true; T().fitPending = false;
  render(); renderInspector(); renderTabs(); persistSoon();
}
function edit(fn, coalesce) {
  const snap = snapshot();
  fn(D());
  if (snapshot() === snap) return;
  pushUndo(snap, coalesce);
  changed();
}
function undo() {
  const t = T();
  if (!t.undo.length) return;
  t.redo.push(snapshot()); t.doc = JSON.parse(t.undo.pop()); t.lastCo = null;
  pruneSel(); changed();
}
function redo() {
  const t = T();
  if (!t.redo.length) return;
  t.undo.push(snapshot()); t.doc = JSON.parse(t.redo.pop());
  pruneSel(); changed();
}
function pruneSel() { const ids = new Set(D().elements.map((e) => e.id)); for (const id of [...T().sel]) if (!ids.has(id)) T().sel.delete(id); }

function nextId(doc = D()) {
  let n = 0;
  for (const e of doc.elements) { const m = /^[a-z]+(\d+)$/.exec(e.id || ''); if (m) n = Math.max(n, +m[1]); }
  return 'e' + (n + 1);
}
function nextRef(prefix, doc = D(), extra = new Set()) {
  if (!prefix) return '';
  const used = new Set(doc.elements.filter((e) => e.type === 'comp').map((e) => e.props?.ref));
  let i = 1;
  while (used.has(prefix + i) || extra.has(prefix + i)) i++;
  return prefix + i;
}
const byId = (id) => D().elements.find((e) => e.id === id);
const selected = () => D().elements.filter((e) => T().sel.has(e.id));

// ---------------------------------------------------------------- persistence (browser autosave)
let persistTimer = 0;
function persistSoon() { clearTimeout(persistTimer); persistTimer = setTimeout(persist, 800); }
function persist() {
  try {
    localStorage.setItem('schematrix-session', JSON.stringify({ cur: S.tabs.indexOf(S.cur),
      tabs: S.tabs.map((t) => ({ doc: t.doc, path: t.path, dirty: t.dirty })) }));
  } catch { /* storage full or blocked: autosave is best effort */ }
}
function restore() {
  try {
    const s = JSON.parse(localStorage.getItem('schematrix-session') || 'null');
    if (s?.tabs?.length) {
      for (const t of s.tabs) { const tab = openTab(t.doc, t.path, false); tab.dirty = t.dirty; }
      switchTab(S.tabs[Math.min(Math.max(0, s.cur), S.tabs.length - 1)]);
      return true;
    }
  } catch { /* ignore a corrupt session */ }
  return false;
}

// ---------------------------------------------------------------- view
const svg = $('#canvas');
function applyView() {
  const v = T().view;
  $('#viewport').setAttribute('transform', `translate(${v.x} ${v.y}) scale(${v.k})`);
  $('#st-zoom').textContent = Math.round(v.k * 100) + '%';
  updateGrid();
}
function pageBox() {
  const d = D(), p = d.page;
  if (p.auto || !p.width) {
    const b = docBBox(), m = p.margin ?? 20;
    return [Math.floor(b[0] - m), Math.floor(b[1] - m), Math.ceil(b[2] - b[0] + 2 * m), Math.ceil(b[3] - b[1] + 2 * m)];
  }
  return [p.x || 0, p.y || 0, p.width, p.height];
}
function fit() {
  const t = T(), r = svg.getBoundingClientRect();
  if (!r.width) return;
  const [x, y, w, h] = pageBox();
  const k = Math.min((r.width - 60) / w, (r.height - 60) / h, 2.5);
  t.view = { k, x: (r.width - w * k) / 2 - x * k, y: (r.height - h * k) / 2 - y * k };
  applyView();
}
function zoomAt(f, cx, cy) {
  T().fitPending = false;
  const v = T().view, r = svg.getBoundingClientRect();
  cx ??= r.width / 2; cy ??= r.height / 2;
  const k = Math.min(12, Math.max(0.08, v.k * f));
  v.x = cx - (cx - v.x) * (k / v.k); v.y = cy - (cy - v.y) * (k / v.k); v.k = k;
  applyView();
}
function updateGrid() {
  const g = D().page.grid || 5, k = T().view?.k || 1;
  let step = g;
  while (step * k < 9) step *= 2;
  const pat = $('#gridpat');
  pat.setAttribute('width', step); pat.setAttribute('height', step);
  pat.firstElementChild.setAttribute('r', Math.max(0.5, 0.9 / Math.sqrt(k)));
}
function toWorld(ev) {
  const r = svg.getBoundingClientRect(), v = T().view;
  return [(ev.clientX - r.left - v.x) / v.k, (ev.clientY - r.top - v.y) / v.k];
}
function toScreen(x, y) {
  const r = svg.getBoundingClientRect(), v = T().view;
  return [r.left + v.x + x * v.k, r.top + v.y + y * v.k];
}

// ---------------------------------------------------------------- bounding boxes
function bboxOf(e, withLabels = true) {
  if (e.type === 'raw' && !e.bbox) {
    const bb = S.rawBB.get(e.id);
    return bb ? [bb[0], bb[1], bb[2], bb[3]] : null;
  }
  return G.elementBBox(e, S.cat, geoOf, withLabels);
}
function docBBox() {
  const bs = D().elements.map((e) => bboxOf(e)).filter(Boolean);
  if (!bs.length) return [0, 0, 400, 300];
  return [Math.min(...bs.map((b) => b[0])), Math.min(...bs.map((b) => b[1])), Math.max(...bs.map((b) => b[2])), Math.max(...bs.map((b) => b[3]))];
}
const union = (bs) => [Math.min(...bs.map((b) => b[0])), Math.min(...bs.map((b) => b[1])), Math.max(...bs.map((b) => b[2])), Math.max(...bs.map((b) => b[3]))];

// ---------------------------------------------------------------- rendering
let themeCss = '';
const scopeCss = (css, scope) => css.replace(/(^|\})\s*([^{}]+)\{/g, (m, a, sel) => `${a}\n${sel.split(',').map((x) => scope + ' ' + x.trim()).join(', ')} {`);
function setThemeCss() {
  const th = D().theme;
  const name = typeof th === 'string' ? th : th?.base || 'instrix';
  const tok = { ...S.info.themes?.instrix, ...(S.info.themes?.[name] || {}), ...(typeof th === 'object' ? th : {}) };
  let css = S.info.css?.[name] || S.info.css?.instrix || '';
  if (typeof th === 'object') for (const [k, v] of Object.entries(th)) if (S.info.themes?.instrix?.[k]) css = css.split(S.info.themes.instrix[k]).join(v);
  css = scopeCss(css, '.sch');
  themeCss = css;
  let st = $('#themecss');
  if (!st) { st = document.createElement('style'); st.id = 'themecss'; document.head.append(st); }
  st.textContent = css;
  document.documentElement.style.setProperty('--pagefill', tok.paper || '#fff');
}

function hitShape(e) {
  if (e.type === 'wire' || e.type === 'arrow') return `<polyline class="hit" points="${e.points.map((p) => p.join(',')).join(' ')}"/>`;
  if (e.type === 'comp' || e.type === 'text') {
    const b = bboxOf(e, false);
    if (!b) return '';
    return `<rect class="hitr" x="${b[0] - 2}" y="${b[1] - 2}" width="${b[2] - b[0] + 4}" height="${b[3] - b[1] + 4}"/>`;
  }
  return '';
}

function render() {
  if (!S.cur) return;
  setThemeCss();
  const d = D();
  let html = '';
  const hops = d.page.hops ? G.hops(d, geoOf) : {};
  for (const e of d.elements) html += `<g class="el" data-id="${e.id}">${hitShape(e)}${G.elementSvg(e, S.cat, geoOf, hops[e.id])}</g>`;
  if (d.page.junctions !== false) {
    const manual = new Set(d.elements.filter((e) => e.type === 'comp' && e.sym === 'dot').map((e) => G.key([e.x, e.y])));
    for (const p of G.junctions(d, geoOf)) if (!manual.has(G.key(p))) html += `<circle class="dot" cx="${p[0]}" cy="${p[1]}" r="3"/>`;
  }
  const content = $('#content');
  content.innerHTML = html;
  for (const e of d.elements) {
    if (e.type === 'raw' && !e.bbox) {
      const g = content.querySelector(`[data-id="${CSS.escape(e.id)}"]`);
      try { const b = g.getBBox(); S.rawBB.set(e.id, [b.x, b.y, b.x + b.width, b.y + b.height]); } catch { /* not laid out */ }
    }
  }
  const [px, py, pw, ph] = pageBox();
  for (const id of ['#page', '#gridrect']) {
    const r = $(id);
    r.setAttribute('x', px); r.setAttribute('y', py); r.setAttribute('width', pw); r.setAttribute('height', ph);
  }
  $('#gridrect').classList.toggle('off', !S.grid);
  $('#empty').hidden = d.elements.length > 0;
  renderOverlay();
  renderStatus();
}

function renderOverlay() {
  const ov = $('#overlay'), t = T(), k = t.view?.k || 1;
  let s = '';
  for (const e of selected()) {
    if (e.type === 'wire' || e.type === 'arrow') {
      s += `<polyline class="selwire" points="${e.points.map((p) => p.join(',')).join(' ')}"/>`;
      if (t.sel.size === 1) e.points.forEach((p, i) => { s += `<circle class="vh h" data-vertex="${i}" data-wid="${e.id}" cx="${p[0]}" cy="${p[1]}" r="${4 / k}"/>`; });
    } else {
      const b = bboxOf(e);
      if (b) s += `<rect class="selbox" x="${b[0] - 3}" y="${b[1] - 3}" width="${b[2] - b[0] + 6}" height="${b[3] - b[1] + 6}"/>`;
      if (e.type === 'rect' && t.sel.size === 1) s += `<rect class="vh h" data-resize="${e.id}" x="${e.x + e.w - 4 / k}" y="${e.y + e.h - 4 / k}" width="${8 / k}" height="${8 / k}"/>`;
    }
  }
  if (S.tool === 'wire' || S.draft?.kind === 'wire') {
    for (const e of D().elements) if (e.type === 'comp' && e.sym !== 'dot') for (const p of Object.values(pinsOf(e))) s += `<circle class="pinmark" cx="${p[0]}" cy="${p[1]}" r="${2.5 / k}"/>`;
  }
  if (S.netHL) for (const p of S.netHL) s += `<circle class="nethl" cx="${p[0]}" cy="${p[1]}" r="${6 / k}"/>`;
  if (S.draft) {
    const pts = draftPath();
    s += `<polyline class="draft" points="${pts.map((p) => p.join(',')).join(' ')}"/>`;
    if (S.draft.snapKind && S.draft.snapKind !== 'grid') { const c = S.draft.cur; s += `<circle class="snapmark" cx="${c[0]}" cy="${c[1]}" r="${6 / k}"/>`; }
  } else if (S.hover && (S.tool === 'wire' || S.tool === 'arrow' || S.tool === 'flag')) {
    const c = S.hover;
    if (S.hoverKind && S.hoverKind !== 'grid') s += `<circle class="snapmark" cx="${c[0]}" cy="${c[1]}" r="${6 / k}"/>`;
    s += `<path class="cross" d="M${c[0] - 8 / k} ${c[1]}h${16 / k}M${c[0]} ${c[1] - 8 / k}v${16 / k}"/>`;
  }
  if (S.placing && S.ghost) s += `<g class="ghost sch">${G.elementSvg(S.ghost, S.cat, geoOf)}</g>`;
  const dr = S.drag;
  if (dr?.kind === 'marquee' || dr?.kind === 'rect') {
    const [a, b] = [dr.start, dr.cur];
    s += `<rect class="marquee" x="${Math.min(a[0], b[0])}" y="${Math.min(a[1], b[1])}" width="${Math.abs(b[0] - a[0])}" height="${Math.abs(b[1] - a[1])}"/>`;
  }
  ov.innerHTML = s;
}

function renderStatus() {
  const names = { select: 'Select', wire: 'Wire', text: 'Text', rect: 'Box', arrow: 'Arrow', flag: 'Net label', place: 'Place' };
  $('#st-tool').textContent = names[S.tool] + (S.placing ? ': ' + (S.cat[S.placing.sym]?.title || '') : '');
  const n = T().sel.size;
  $('#st-sel').textContent = n ? `${n} selected` : `${D().elements.length} elements`;
  const hints = {
    select: '<kbd>Drag</kbd> move · wires stretch (<kbd>Alt</kbd>: whole) · <kbd>R</kbd> rotate · <kbd>M</kbd> mirror · <kbd>E</kbd> accent · <kbd>Shift</kbd>-click add · drag empty to box-select',
    wire: S.draft ? '<kbd>Click</kbd> corner · ends on a pin or wire · <kbd>/</kbd> elbow direction · <kbd>Enter</kbd>/<kbd>Esc</kbd> finish · <kbd>Backspace</kbd> undo corner'
      : '<kbd>Click</kbd> to start a wire · pins and wires snap', arrow: '<kbd>Click</kbd> points · <kbd>Enter</kbd>/<kbd>Esc</kbd> finish',
    place: '<kbd>Click</kbd> to place · <kbd>R</kbd> rotate · <kbd>M</kbd> mirror · <kbd>Esc</kbd> done',
    text: '<kbd>Click</kbd> to add a text', rect: '<kbd>Drag</kbd> to draw a group box', flag: '<kbd>Click</kbd> a wire end or pin to name its net',
  };
  $('#hint').innerHTML = hints[S.placing ? 'place' : S.tool] || '';
}

// ---------------------------------------------------------------- palette
function symThumb(entry, props) {
  const g = entry.geometry;
  const c = { id: 't', type: 'comp', sym: entry.name, x: 0, y: 0, rot: 0, props: props || {}, hide_labels: true };
  const body = g.prims.map((p) => G.primSvg(p, c, '')).join('');
  const [x0, y0, x1, y1] = g.bbox, pad = 4;
  return `<svg class="schp" viewBox="${x0 - pad} ${y0 - pad} ${x1 - x0 + 2 * pad} ${y1 - y0 + 2 * pad}" preserveAspectRatio="xMidYMid meet">${body}</svg>`;
}
function buildPalette(filter = '') {
  const pal = $('#palette'), f = filter.trim().toLowerCase();
  pal.innerHTML = '';
  let lastCat = null, grid = null;
  for (const e of S.catList) {
    if (f && !(e.title.toLowerCase().includes(f) || e.name.includes(f) || e.category.toLowerCase().includes(f))) continue;
    if (e.category !== lastCat) {
      lastCat = e.category;
      pal.insertAdjacentHTML('beforeend', `<div class="cat">${G.esc(e.category)}</div>`);
      grid = document.createElement('div'); grid.className = 'syms'; pal.append(grid);
    }
    const b = document.createElement('div');
    b.className = 'sym' + (S.placing?.sym === e.name ? ' on' : '');
    b.title = `${e.title}${e.help ? ' — ' + e.help : ''}\npins: ${Object.keys(e.geometry.pins).join(', ')}`;
    b.innerHTML = symThumb(e) + `<span>${G.esc(e.title)}</span>`;
    b.onclick = () => startPlacing(e.name);
    grid.append(b);
  }
}

// ---------------------------------------------------------------- tools
function setTool(t) {
  if (S.draft) finishDraft();
  S.tool = t; S.placing = t === 'place' ? S.placing : null; S.ghost = null;
  svg.className.baseVal = 'tool-' + t;
  $$('#tools button').forEach((b) => b.classList.toggle('on', b.dataset.tool === t));
  $$('.sym').forEach((b) => b.classList.remove('on'));
  renderOverlay(); renderStatus();
}
function startPlacing(sym, props = {}) {
  setTool('place');
  S.placing = { sym, props, rot: 0, mirror: false };
  buildPalette($('#symsearch').value);
  updateGhost(S.mouse);
  svg.focus();
}
function updateGhost(w) {
  if (!S.placing) return;
  const g = D().page.grid || 5;
  const { sym, props, rot, mirror } = S.placing;
  S.ghost = { id: 'ghost', type: 'comp', sym, x: snapTo(w[0], g), y: snapTo(w[1], g), rot, mirror, props: { ...props }, style: S.style };
  renderOverlay();
}
function placeAt(w) {
  const { sym, props, rot, mirror } = S.placing, c = S.cat[sym], g = D().page.grid || 5;
  edit((d) => {
    const el = { id: nextId(d), type: 'comp', sym, x: snapTo(w[0], g), y: snapTo(w[1], g), rot, mirror, props: { ...props }, style: S.style };
    if (c.props.ref && !props.ref) el.props.ref = nextRef(c.prefix, d);
    d.elements.push(el);
    T().sel = new Set([el.id]);
  });
}

// snapping for wire ends: pins and wire vertices first, then wire segments, then the grid
function snapPoint(w, excludeWire) {
  const k = T().view.k, R = 9 / k, g = D().page.grid || 5;
  let best = null, bd = R;
  for (const e of D().elements) {
    if (e.type === 'comp') for (const p of Object.values(pinsOf(e))) { const dd = Math.hypot(p[0] - w[0], p[1] - w[1]); if (dd < bd) { bd = dd; best = [p, 'pin']; } }
    if (e.type === 'wire' && e.id !== excludeWire) for (const p of e.points) { const dd = Math.hypot(p[0] - w[0], p[1] - w[1]); if (dd < bd) { bd = dd; best = [p, 'wire']; } }
  }
  if (best) return { p: [...best[0]], kind: best[1] };
  for (const e of D().elements) {
    if (e.type !== 'wire' || e.id === excludeWire) continue;
    for (let i = 0; i + 1 < e.points.length; i++) {
      const [a, b] = [e.points[i], e.points[i + 1]];
      if (a[1] === b[1] && Math.abs(w[1] - a[1]) < 6 / k && w[0] > Math.min(a[0], b[0]) && w[0] < Math.max(a[0], b[0])) return { p: [snapTo(w[0], g), a[1]], kind: 'seg' };
      if (a[0] === b[0] && Math.abs(w[0] - a[0]) < 6 / k && w[1] > Math.min(a[1], b[1]) && w[1] < Math.max(a[1], b[1])) return { p: [a[0], snapTo(w[1], g)], kind: 'seg' };
    }
  }
  return { p: [snapTo(w[0], g), snapTo(w[1], g)], kind: 'grid' };
}
function elbow(a, c, prevDir) {
  if (a[0] === c[0] || a[1] === c[1]) return [];
  let mode = S.wireMode;
  if (mode === 'auto') mode = prevDir === 'h' ? 'vh' : prevDir === 'v' ? 'hv' : Math.abs(c[0] - a[0]) >= Math.abs(c[1] - a[1]) ? 'hv' : 'vh';
  return mode === 'hv' ? [[c[0], a[1]]] : [[a[0], c[1]]];
}
function draftPath() {
  const dr = S.draft, pts = dr.pts, a = pts[pts.length - 1];
  if (dr.kind === 'arrow') return [...pts, dr.cur];
  let prevDir = null;
  if (pts.length >= 2) { const p = pts[pts.length - 2]; prevDir = p[1] === a[1] ? 'h' : p[0] === a[0] ? 'v' : null; }
  return [...pts, ...elbow(a, dr.cur, prevDir), dr.cur];
}
function simplify(P) {
  const out = [];
  for (const p of P) { if (!out.length || G.key(out[out.length - 1]) !== G.key(p)) out.push([p[0], p[1]]); }
  for (let i = out.length - 2; i >= 1; i--) {
    const [a, b, c] = [out[i - 1], out[i], out[i + 1]];
    if ((a[0] === b[0] && b[0] === c[0]) || (a[1] === b[1] && b[1] === c[1])) out.splice(i, 1);
  }
  return out;
}
function draftClick(w, ev) {
  const sn = S.draft?.kind === 'arrow' || S.tool === 'arrow' ? { p: [snapTo(w[0], D().page.grid || 5), snapTo(w[1], D().page.grid || 5)], kind: 'grid' } : snapPoint(w);
  if (!S.draft) { S.draft = { kind: S.tool, pts: [sn.p], cur: sn.p, snapKind: sn.kind }; renderOverlay(); renderStatus(); return; }
  const dr = S.draft;
  dr.cur = sn.p;
  const path = draftPath();
  const last = dr.pts[dr.pts.length - 1];
  if (G.key(last) === G.key(sn.p) && dr.pts.length >= 2) { finishDraft(); return; }
  dr.pts = path;
  if (dr.kind === 'wire' && sn.kind !== 'grid' && dr.pts.length >= 2) finishDraft();
  else renderOverlay();
}
function finishDraft() {
  const dr = S.draft;
  S.draft = null;
  if (!dr) return;
  const P = dr.kind === 'arrow' ? dr.pts : simplify(dr.pts);
  if (P.length >= 2) {
    edit((d) => {
      const el = { id: nextId(d), type: dr.kind, points: P, style: dr.kind === 'arrow' ? S.style || 'acc' : S.style };
      d.elements.push(el);
    });
  } else render();
  renderStatus();
}

// ---------------------------------------------------------------- moving with rubber-banding
function startMove(w) {
  const t = T(), ids = t.sel, orig = new Map();
  for (const e of selected()) orig.set(e.id, clone(e));
  const pinKeys = new Set();
  for (const e of selected()) if (e.type === 'comp') for (const p of Object.values(pinsOf(e))) pinKeys.add(G.key(p));
  const attached = [];
  for (const e of D().elements) {
    if (e.type !== 'wire' || ids.has(e.id) || e.points.length < 2) continue;
    const n = e.points.length;
    const a0 = pinKeys.has(G.key(e.points[0])), a1 = pinKeys.has(G.key(e.points[n - 1]));
    if (a0 || a1) attached.push({ id: e.id, orig: clone(e.points), a0, a1 });
  }
  S.drag = { kind: 'move', start: w, orig, attached, snap: snapshot(), moved: false };
}
function applyMove(dx, dy) {
  const dr = S.drag;
  for (const [id, o] of dr.orig) {
    const e = byId(id);
    if (!e) continue;
    if ('x' in o) { e.x = o.x + dx; e.y = o.y + dy; }
    if (o.points) e.points = o.points.map(([x, y]) => [x + dx, y + dy]);
  }
  for (const a of dr.attached) { const e = byId(a.id); if (e) e.points = rubber(a, dx, dy); }
}
// a wire with one or both ends on something moving by (dx, dy): drag those ends and keep the wire orthogonal
function rubber(a, dx, dy) {
  let P = clone(a.orig);
  if (a.a0 && a.a1) return P.map(([x, y]) => [x + dx, y + dy]);
  if (a.a1) P.reverse();
  // P[0] is the moving end
  if (P.length === 2 && (P[0][0] === P[1][0] || P[0][1] === P[1][1]) && (dx || dy)) {
    const horiz = P[0][1] === P[1][1];
    const m = horiz ? snapTo((P[0][0] + P[1][0]) / 2, D().page.grid || 5) : snapTo((P[0][1] + P[1][1]) / 2, D().page.grid || 5);
    P = horiz ? [P[0], [m, P[0][1]], [m, P[1][1]], P[1]] : [P[0], [P[0][0], m], [P[1][0], m], P[1]];
  }
  const horiz = P[0][1] === P[1][1], vert = P[0][0] === P[1][0];
  P[0] = [P[0][0] + dx, P[0][1] + dy];
  if (P.length > 2) {
    if (horiz && !vert) P[1] = [P[1][0], P[1][1] + dy];
    else if (vert && !horiz) P[1] = [P[1][0] + dx, P[1][1]];
  }
  if (a.a1) P.reverse();
  return P;
}

// ---------------------------------------------------------------- KiCad-style wire dragging
// grabbing a wire end stretches it (along its last segment, then an elbow); grabbing a segment slides it
// square to itself while its neighbours stretch, a connected end stays put behind a new stub, and wires
// that end on the moving part (T branches) follow
function connectedAt(p, wid) {
  const k = G.key(p);
  for (const e of D().elements) {
    if (e.type === 'comp' && (e.sym === 'dot' ? G.key([e.x, e.y]) === k : Object.values(pinsOf(e)).some((q) => G.key(q) === k))) return true;
    if (e.type !== 'wire' || e.id === wid) continue;
    if (e.points.some((q) => G.key(q) === k)) return true;
    for (let i = 0; i + 1 < e.points.length; i++) if (G.onSegment(p, e.points[i], e.points[i + 1])) return true;
  }
  return false;
}
function segDist(p, a, b) {
  const [vx, vy] = [b[0] - a[0], b[1] - a[1]], L = vx * vx + vy * vy;
  const t = L ? Math.max(0, Math.min(1, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / L)) : 0;
  return Math.hypot(p[0] - a[0] - t * vx, p[1] - a[1] - t * vy);
}
function startWireDrag(e, w, end) {
  const P = e.points, n = P.length, R = 8 / T().view.k;
  if (end === undefined) for (const i of [0, n - 1]) if (Math.hypot(P[i][0] - w[0], P[i][1] - w[1]) < R) { end = i; break; }
  const base = { id: e.id, start: w, orig: clone(P), snap: snapshot(), attached: [] };
  if (end !== undefined) { S.drag = { ...base, kind: 'wend', end }; return; }
  let seg = 0, bd = Infinity;
  for (let i = 0; i + 1 < n; i++) { const d = segDist(w, P[i], P[i + 1]); if (d < bd) { bd = d; seg = i; } }
  const [a, b] = [P[seg], P[seg + 1]];
  const stub0 = seg === 0 && connectedAt(P[0], e.id), stub1 = seg + 1 === n - 1 && connectedAt(P[n - 1], e.id);
  // other wires with an end on the moving segment (or on one of its moving corners) come along
  for (const o of D().elements) {
    if (o.type !== 'wire' || o.id === e.id || o.points.length < 2) continue;
    const on = (q) => (G.onSegment(q, a, b) || (G.key(q) === G.key(a) && !stub0) || (G.key(q) === G.key(b) && !stub1));
    const m = o.points.length, a0 = on(o.points[0]), a1 = on(o.points[m - 1]);
    if (a0 || a1) base.attached.push({ id: o.id, orig: clone(o.points), a0, a1 });
  }
  S.drag = { ...base, kind: 'wseg', seg, stub0, stub1, horiz: a[1] === b[1], vert: a[0] === b[0] };
}
function applyWireDrag(w) {
  const dr = S.drag, e = byId(dr.id), g = D().page.grid || 5, O = dr.orig, n = O.length;
  if (!e) return;
  if (dr.kind === 'wend') {
    const c = snapPoint(w, e.id).p;
    const P = dr.end === 0 ? clone(O) : clone(O).reverse();      // P[0] is the grabbed end
    const a = P[1], dir = P[0][1] === a[1] ? 'h' : P[0][0] === a[0] ? 'v' : null;
    const corner = a[0] === c[0] || a[1] === c[1] ? [] : dir === 'v' ? [[a[0], c[1]]] : [[c[0], a[1]]];
    const Q = [c, ...corner, ...P.slice(1)];
    e.points = dr.end === 0 ? Q : Q.reverse();
    return;
  }
  let dx = snapTo(w[0] - dr.start[0], g), dy = snapTo(w[1] - dr.start[1], g);
  if (dr.horiz) dx = 0; else if (dr.vert) dy = 0;
  const i = dr.seg, Q = clone(O), mv = (p) => [p[0] + dx, p[1] + dy];
  Q[i] = mv(Q[i]); Q[i + 1] = mv(Q[i + 1]);
  if (dr.stub1) Q.push(clone(O[n - 1]));
  if (dr.stub0) Q.unshift(clone(O[0]));
  e.points = Q;
  for (const a of dr.attached) { const o = byId(a.id); if (o) o.points = rubber(a, dx, dy); }
}
function endDrag() {
  const dr = S.drag;
  S.drag = null;
  if (!dr) return;
  if (['move', 'vertex', 'label', 'resize', 'wend', 'wseg'].includes(dr.kind)) {
    for (const a of dr.attached || []) { const e = byId(a.id); if (e) e.points = simplify(e.points); }
    if (['vertex', 'wend', 'wseg'].includes(dr.kind)) {
      const e = byId(dr.id);
      if (e) e.points = simplify(e.points);
      if (e?.type === 'wire' && e.points.length < 2) { D().elements = D().elements.filter((x) => x !== e); T().sel.delete(e.id); }
    }
    if (snapshot() !== dr.snap) { pushUndo(dr.snap); changed(); } else render();
  } else if (dr.kind === 'marquee') {
    const [a, b] = [dr.start, dr.cur];
    const box = [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[0], b[0]), Math.max(a[1], b[1])];
    const crossing = b[0] < a[0];          // right-to-left drag: anything touched
    if (!dr.additive) T().sel.clear();
    for (const e of D().elements) {
      const bb = bboxOf(e, false);
      if (!bb) continue;
      const inside = bb[0] >= box[0] && bb[1] >= box[1] && bb[2] <= box[2] && bb[3] <= box[3];
      const touch = !(bb[2] < box[0] || bb[0] > box[2] || bb[3] < box[1] || bb[1] > box[3]);
      if (inside || (crossing && touch)) T().sel.add(e.id);
    }
    render(); renderInspector();
  } else if (dr.kind === 'rect') {
    const [a, b] = [dr.start, dr.cur];
    const w = Math.abs(b[0] - a[0]), h = Math.abs(b[1] - a[1]);
    if (w > 4 && h > 4) {
      edit((d) => {
        const el = { id: nextId(d), type: 'rect', x: Math.min(a[0], b[0]), y: Math.min(a[1], b[1]), w, h, cls: 'grp', rx: 4, label: '' };
        d.elements.unshift(el); T().sel = new Set([el.id]);
      });
      setTool('select');
    } else render();
  }
}

// ---------------------------------------------------------------- pointer
svg.addEventListener('pointerdown', (ev) => {
  svg.focus();
  closeMenus();
  const w = toWorld(ev);
  if (ev.button === 1 || (ev.button === 0 && S.space)) {
    S.drag = { kind: 'pan', sx: ev.clientX, sy: ev.clientY, vx: T().view.x, vy: T().view.y };
    svg.classList.add('panning'); svg.setPointerCapture(ev.pointerId); ev.preventDefault(); return;
  }
  if (ev.button === 2) { if (S.draft) finishDraft(); return; }
  if (ev.button !== 0) return;
  svg.setPointerCapture(ev.pointerId);
  const g = D().page.grid || 5;
  if (S.tool === 'place') { placeAt(w); return; }
  if (S.tool === 'wire' || S.tool === 'arrow') { draftClick(w, ev); return; }
  if (S.tool === 'flag') { placeFlag(w); return; }
  if (S.tool === 'text') {
    edit((d) => { const el = { id: nextId(d), type: 'text', x: snapTo(w[0], g), y: snapTo(w[1], g), text: 'Text', cls: 'lbl', anchor: 'start' }; d.elements.push(el); T().sel = new Set([el.id]); });
    const id = [...T().sel][0]; setTool('select'); inlineEdit(byId(id), 'text'); return;
  }
  if (S.tool === 'rect') { const p = [snapTo(w[0], g), snapTo(w[1], g)]; S.drag = { kind: 'rect', start: p, cur: p }; return; }
  // select tool
  const h = ev.target.closest('.h');
  if (h?.dataset.vertex !== undefined) {
    const e = byId(h.dataset.wid), i = +h.dataset.vertex;
    if (e.type === 'wire' && (i === 0 || i === e.points.length - 1)) { startWireDrag(e, w, i); return; }
    S.drag = { kind: 'vertex', id: h.dataset.wid, idx: i, snap: snapshot() }; return;
  }
  if (h?.dataset.resize) { S.drag = { kind: 'resize', id: h.dataset.resize, snap: snapshot() }; return; }
  const elg = ev.target.closest('#content [data-id]');
  const id = elg?.dataset.id;
  const t = T();
  if (id) {
    const lab = ev.target.closest('[data-label]');
    if (lab && t.sel.has(id) && t.sel.size === 1 && byId(id).type === 'comp') {
      const e = byId(id);
      S.drag = { kind: 'label', id, start: w, orig: e.label_offset ? [...e.label_offset] : [0, 0], snap: snapshot() }; return;
    }
    if (ev.shiftKey || ev.ctrlKey || ev.metaKey) { if (t.sel.has(id)) t.sel.delete(id); else t.sel.add(id); render(); renderInspector(); return; }
    const e = byId(id);
    // a lone wire drags KiCad-style; Alt-drag, or a wire inside a bigger selection, moves whole
    if (e.type === 'wire' && !ev.altKey && !(t.sel.has(id) && t.sel.size > 1)) {
      if (!t.sel.has(id) || t.sel.size !== 1) { t.sel = new Set([id]); render(); renderInspector(); }
      startWireDrag(e, w); return;
    }
    if (!t.sel.has(id)) { t.sel = new Set([id]); render(); renderInspector(); }
    startMove(w);
    return;
  }
  S.drag = { kind: 'marquee', start: w, cur: w, additive: ev.shiftKey };
  if (!ev.shiftKey && t.sel.size) { t.sel.clear(); render(); renderInspector(); }
});

svg.addEventListener('pointermove', (ev) => {
  if (!S.cur?.view) return;
  const w = toWorld(ev);
  S.mouse = w;
  $('#st-xy').textContent = `${Math.round(w[0])}, ${Math.round(w[1])}`;
  const dr = S.drag, g = D().page.grid || 5;
  if (dr?.kind === 'pan') { T().fitPending = false; T().view.x = dr.vx + ev.clientX - dr.sx; T().view.y = dr.vy + ev.clientY - dr.sy; applyView(); return; }
  if (S.placing) { updateGhost(w); return; }
  if (S.draft) {
    const sn = S.draft.kind === 'arrow' ? { p: [snapTo(w[0], g), snapTo(w[1], g)], kind: 'grid' } : snapPoint(w);
    S.draft.cur = sn.p; S.draft.snapKind = sn.kind; renderOverlay(); return;
  }
  if (!dr && (S.tool === 'wire' || S.tool === 'flag' || S.tool === 'arrow')) {
    const sn = S.tool === 'arrow' ? { p: [snapTo(w[0], g), snapTo(w[1], g)], kind: 'grid' } : snapPoint(w);
    S.hover = sn.p; S.hoverKind = sn.kind; renderOverlay(); return;
  }
  if (!dr) return;
  if (dr.kind === 'move') {
    const dx = snapTo(w[0] - dr.start[0], g), dy = snapTo(w[1] - dr.start[1], g);
    if (dx !== dr.dx || dy !== dr.dy) { dr.dx = dx; dr.dy = dy; applyMove(dx, dy); render(); }
  } else if (dr.kind === 'wend' || dr.kind === 'wseg') {
    applyWireDrag(w); render();
  } else if (dr.kind === 'vertex') {
    const e = byId(dr.id), sn = e.type === 'wire' ? snapPoint(w, e.id) : { p: [snapTo(w[0], g), snapTo(w[1], g)] };
    e.points[dr.idx] = sn.p; render();
  } else if (dr.kind === 'label') {
    const e = byId(dr.id);
    e.label_offset = [dr.orig[0] + Math.round(w[0] - dr.start[0]), dr.orig[1] + Math.round(w[1] - dr.start[1])]; render();
  } else if (dr.kind === 'resize') {
    const e = byId(dr.id);
    e.w = Math.max(10, snapTo(w[0], g) - e.x); e.h = Math.max(10, snapTo(w[1], g) - e.y); render();
  } else if (dr.kind === 'marquee') { dr.cur = w; renderOverlay(); } else if (dr.kind === 'rect') { dr.cur = [snapTo(w[0], g), snapTo(w[1], g)]; renderOverlay(); }
});

svg.addEventListener('pointerup', () => {
  if (S.drag?.kind === 'pan') { S.drag = null; svg.classList.remove('panning'); return; }
  endDrag();
});
svg.addEventListener('contextmenu', (ev) => ev.preventDefault());
svg.addEventListener('dblclick', (ev) => {
  if (S.tool !== 'select') { if (S.draft) finishDraft(); return; }
  const id = ev.target.closest('#content [data-id]')?.dataset.id;
  if (!id) return;
  const e = byId(id), lab = ev.target.closest('[data-label]')?.dataset.label;
  if (e.type === 'text') inlineEdit(e, 'text');
  else if (e.type === 'comp') {
    const key = lab || { flag: 'label', terminal: 'label', block: 'title', rail: 'net' }[e.sym] || 'value';
    inlineEdit(e, key);
  } else if (e.type === 'wire') {
    // insert a vertex on the clicked segment
    const w = toWorld(ev), gg = D().page.grid || 5, p = [snapTo(w[0], gg), snapTo(w[1], gg)];
    edit(() => {
      for (let i = 0; i + 1 < e.points.length; i++) if (G.onSegment(p, e.points[i], e.points[i + 1], 6)) { e.points.splice(i + 1, 0, p); break; }
    });
  } else if (e.type === 'rect') inlineEdit(e, 'label');
});
svg.addEventListener('wheel', (ev) => {
  ev.preventDefault();
  const r = svg.getBoundingClientRect();
  if (ev.ctrlKey || ev.metaKey || Math.abs(ev.deltaY) >= 50 || ev.deltaMode) zoomAt(Math.exp(-ev.deltaY * (ev.ctrlKey ? 0.01 : 0.0015)), ev.clientX - r.left, ev.clientY - r.top);
  else { T().fitPending = false; T().view.x -= ev.deltaX; T().view.y -= ev.deltaY; applyView(); }
}, { passive: false });
new ResizeObserver(() => { if (S.cur?.view) applyView(); else if (S.cur) fit(); }).observe(svg);

// ---------------------------------------------------------------- net labels
async function placeFlag(w) {
  const sn = snapPoint(w);
  const name = await ask('Net name', S.lastFlag);
  if (!name) return;
  S.lastFlag = name;
  let side = 'left';
  for (const e of D().elements) {
    if (e.type !== 'wire') continue;
    const P = e.points, n = P.length;
    if (G.key(P[0]) === G.key(sn.p) && n > 1 && P[1][0] < sn.p[0]) side = 'right';
    if (G.key(P[n - 1]) === G.key(sn.p) && n > 1 && P[n - 2][0] < sn.p[0]) side = 'right';
  }
  edit((d) => { const el = { id: nextId(d), type: 'comp', sym: 'flag', x: sn.p[0], y: sn.p[1], rot: 0, mirror: false, props: { label: name, side }, style: '' }; d.elements.push(el); T().sel = new Set([el.id]); });
}

// ---------------------------------------------------------------- inline text editing
function inlineEdit(e, key) {
  const ta = $('#inlineedit');
  let value, anchor, cls;
  if (e.type === 'text') { value = e.text; anchor = [e.x, e.y]; cls = e.cls; } else if (e.type === 'rect') { value = e.label || ''; anchor = [e.x + 4, e.y + 12]; } else {
    const c = S.cat[e.sym];
    value = String(e.props?.[key] ?? c?.props[key]?.default ?? '');
    const lb = G.labelBlock(e, c, geoOf(e)).find((l) => l[5] === key);
    anchor = lb ? [lb[0], lb[1]] : [e.x, e.y];
  }
  const [sx, sy] = toScreen(anchor[0], anchor[1]), k = T().view.k;
  ta.hidden = false;
  ta.value = value;
  ta.style.left = Math.max(4, sx - 4) + 'px'; ta.style.top = (sy - 16 * Math.max(1, k)) + 'px';
  ta.style.fontSize = Math.max(11, 12 * k) + 'px';
  ta.style.width = Math.max(120, (Math.max(...value.split('\n').map((l) => l.length)) + 4) * 7.5 * Math.max(1, k)) + 'px';
  ta.rows = Math.max(1, value.split('\n').length);
  ta.focus(); ta.select();
  const done = (ok) => {
    ta.onkeydown = ta.onblur = null; ta.hidden = true;
    if (ok && ta.value !== value) edit(() => {
      if (e.type === 'text') e.text = ta.value; else if (e.type === 'rect') e.label = ta.value;
      else { e.props = { ...e.props, [key]: ta.value }; if (key === 'label' && e.sym === 'flag') S.lastFlag = ta.value; }
    });
    svg.focus();
  };
  ta.onkeydown = (ev) => {
    ev.stopPropagation();
    if (ev.key === 'Escape') done(false);
    else if (ev.key === 'Enter' && !ev.shiftKey) { ev.preventDefault(); done(true); } else ta.rows = Math.max(1, ta.value.split('\n').length);
  };
  ta.onblur = () => done(true);
}

// ---------------------------------------------------------------- selection operations
function selCenter() {
  const bs = selected().map((e) => bboxOf(e, false)).filter(Boolean);
  const b = union(bs), g = D().page.grid || 5;
  return [snapTo((b[0] + b[2]) / 2, g), snapTo((b[1] + b[3]) / 2, g)];
}
function transformSel(kind) {
  if (S.placing) {
    if (kind === 'rot') S.placing.rot = (S.placing.rot + 90) % 360;
    else { S.placing.rot = (360 - S.placing.rot) % 360; S.placing.mirror = !S.placing.mirror; }
    updateGhost(S.mouse); return;
  }
  const sel = selected();
  if (!sel.length) return;
  const single = sel.length === 1 && sel[0].type === 'comp';
  const c = single ? [sel[0].x, sel[0].y] : selCenter();
  const f = kind === 'rot' ? ([x, y]) => [c[0] - (y - c[1]), c[1] + (x - c[0])] : ([x, y]) => [2 * c[0] - x, y];
  edit(() => {
    for (const e of sel) {
      if (e.type === 'comp') {
        [e.x, e.y] = f([e.x, e.y]);
        if (kind === 'rot') e.rot = ((e.rot || 0) + 90) % 360; else { e.rot = (360 - (e.rot || 0)) % 360; e.mirror = !e.mirror; }
        if (e.label_offset) e.label_offset = kind === 'rot' ? [-e.label_offset[1], e.label_offset[0]] : [-e.label_offset[0], e.label_offset[1]];
      } else if (e.points) e.points = e.points.map(f);
      else if (e.type === 'text') {
        [e.x, e.y] = f([e.x, e.y]);
        if (kind === 'mir' && e.anchor !== 'middle') e.anchor = e.anchor === 'end' ? 'start' : 'end';
      } else if (e.type === 'rect') {
        const pts = [f([e.x, e.y]), f([e.x + e.w, e.y + e.h])];
        e.x = Math.min(pts[0][0], pts[1][0]); e.y = Math.min(pts[0][1], pts[1][1]);
        e.w = Math.abs(pts[1][0] - pts[0][0]); e.h = Math.abs(pts[1][1] - pts[0][1]);
      }
    }
  });
}
function toggleAccent() {
  const sel = selected().filter((e) => e.type === 'comp' || e.type === 'wire' || e.type === 'arrow');
  if (!sel.length) { setStyle(S.style === 'acc' ? '' : 'acc'); return; }
  const on = !sel.every((e) => (e.style || '').split(' ').includes('acc'));
  edit(() => { for (const e of sel) { const t = (e.style || '').split(' ').filter((s) => s && s !== 'acc'); if (on) t.push('acc'); e.style = t.join(' '); } });
}
function del() {
  const t = T();
  if (!t.sel.size) return;
  edit((d) => { d.elements = d.elements.filter((e) => !t.sel.has(e.id)); });
  t.sel.clear(); renderInspector();
}
function nudge(dx, dy) {
  if (!T().sel.size) return;
  edit(() => {
    for (const e of selected()) { if ('x' in e) { e.x += dx; e.y += dy; } if (e.points) e.points = e.points.map(([x, y]) => [x + dx, y + dy]); }
  }, 'nudge');
}
function reorder(front) {
  const t = T();
  edit((d) => {
    const s = d.elements.filter((e) => t.sel.has(e.id)), r = d.elements.filter((e) => !t.sel.has(e.id));
    d.elements = front ? [...r, ...s] : [...s, ...r];
  });
}

// clipboard: element JSON, also on the system clipboard so it pastes across tabs and windows
function copySel() {
  const els = selected();
  if (!els.length) return false;
  const text = JSON.stringify({ schematrix: 1, elements: els });
  S.clip = text;
  navigator.clipboard?.writeText(text).catch(() => {});
  return true;
}
async function paste() {
  let text = S.clip;
  try { const t = await navigator.clipboard.readText(); if (t && t.includes('"schematrix"')) text = t; } catch { /* clipboard permission */ }
  if (!text) return;
  let data;
  try { data = JSON.parse(text); } catch { return; }
  if (!data?.elements) return;
  const els = clone(data.elements);
  const off = (D().page.grid || 5) * 4;
  edit((d) => {
    const sel = new Set(), refs = new Set();
    for (const e of els) {
      e.id = nextId(d);
      if ('x' in e) { e.x += off; e.y += off; }
      if (e.points) e.points = e.points.map(([x, y]) => [x + off, y + off]);
      if (e.type === 'comp' && e.props?.ref && d.elements.some((o) => o.props?.ref === e.props.ref)) {
        e.props.ref = nextRef(S.cat[e.sym]?.prefix || e.props.ref.replace(/\d+$/, ''), d, refs);
      }
      if (e.props?.ref) refs.add(e.props.ref);
      d.elements.push(e); sel.add(e.id);
    }
    T().sel = sel;
  });
}

// ---------------------------------------------------------------- inspector
function field(label, input) {
  const d = document.createElement('div');
  d.className = 'f';
  const l = document.createElement('label'); l.textContent = label;
  d.append(l, input);
  return d;
}
function inp(value, onChange, { type = 'text', mono = false, step, coalesce } = {}) {
  const i = document.createElement('input');
  i.type = type; i.value = value ?? '';
  if (mono) i.className = 'mono';
  if (step) i.step = step;
  i.onchange = () => onChange(type === 'number' ? Number(i.value) : i.value);
  if (coalesce) i.oninput = () => onChange(type === 'number' ? Number(i.value) : i.value, true);
  i.onkeydown = (ev) => { ev.stopPropagation(); if (ev.key === 'Enter') i.blur(); };
  return i;
}
function sel_(value, options, onChange) {
  const s = document.createElement('select');
  for (const o of options) { const [v, t] = Array.isArray(o) ? o : [o, o]; const op = new Option(t, v); if (String(v) === String(value)) op.selected = true; s.append(op); }
  s.onchange = () => onChange(s.value);
  return s;
}
function chk(value, onChange) {
  const c = document.createElement('input');
  c.type = 'checkbox'; c.checked = !!value; c.onchange = () => onChange(c.checked);
  return c;
}
function pair(a, b) { const d = document.createElement('div'); d.className = 'pair'; d.append(a, b); return d; }
function btns(list) {
  const d = document.createElement('div'); d.className = 'btns';
  for (const [t, fn, cls] of list) { const b = document.createElement('button'); b.textContent = t; b.onclick = fn; if (cls) b.className = cls; d.append(b); }
  return d;
}
function seg(value, options, onChange) {
  const d = document.createElement('div'); d.className = 'seg';
  for (const [v, t] of options) { const b = document.createElement('button'); b.textContent = t; if (v === value) b.className = 'on'; b.onclick = () => onChange(v); d.append(b); }
  return d;
}
const STYLES = [['', 'Ink'], ['acc', 'Accent'], ['para', 'Dash'], ['acc para', 'Acc·dash']];
const sect = (t) => { const d = document.createElement('div'); d.className = 'sect'; d.textContent = t; return d; };

function renderInspector() {
  const p = $('#pane-props');
  if (!S.cur) return;
  p.innerHTML = '';
  const sel = selected();
  const head = (title, sub) => { p.insertAdjacentHTML('beforeend', `<h3>${title}</h3>${sub ? `<div class="sub">${sub}</div>` : ''}`); };
  const set = (e, k, coalesce) => (v, co) => edit(() => { e[k] = v; }, co ? coalesce || `${e.id}.${k}` : undefined);
  const setp = (e, k) => (v, co) => edit(() => { e.props = { ...e.props, [k]: v }; }, co ? `${e.id}.p.${k}` : undefined);
  if (!sel.length) {
    const d = D(), pg = d.page;
    head('Document', `${d.elements.length} elements`);
    p.append(field('Title', inp(d.meta.title, (v) => edit(() => { d.meta.title = v; }))));
    const ta = document.createElement('textarea'); ta.value = d.meta.description || ''; ta.rows = 3;
    ta.onchange = () => edit(() => { d.meta.description = ta.value; }); ta.onkeydown = (ev) => ev.stopPropagation();
    p.append(field('Description', ta));
    p.append(sect('Page'));
    p.append(field('Auto size', chk(pg.auto, (v) => edit(() => { pg.auto = v; if (!v && !pg.width) { const b = pageBox(); Object.assign(pg, { x: b[0], y: b[1], width: b[2], height: b[3] }); } }))));
    if (!pg.auto) p.append(field('Size', pair(inp(pg.width, set(pg, 'width'), { type: 'number', mono: true }), inp(pg.height, set(pg, 'height'), { type: 'number', mono: true }))));
    if (!pg.auto) p.append(field('Origin', pair(inp(pg.x || 0, set(pg, 'x'), { type: 'number', mono: true }), inp(pg.y || 0, set(pg, 'y'), { type: 'number', mono: true }))));
    p.append(field('Margin', inp(pg.margin ?? 20, set(pg, 'margin'), { type: 'number', mono: true })));
    p.append(field('Grid', sel_(pg.grid || 5, [1, 2, 5, 10, 20], (v) => edit(() => { pg.grid = Number(v); }))));
    p.append(field('Junctions', chk(pg.junctions !== false, (v) => edit(() => { pg.junctions = v; }))));
    p.append(field('Wire hops', chk(!!pg.hops, (v) => edit(() => { pg.hops = v; }))));
    p.append(field('Theme', sel_(typeof d.theme === 'string' ? d.theme : 'custom', [...Object.keys(S.info.themes || {}), ...(typeof d.theme === 'object' ? ['custom'] : [])], (v) => edit(() => { d.theme = v; }))));
    p.append(btns([['Fit page to drawing', () => edit(() => {
      const bb = docBBox(), m = pg.margin ?? 20;
      Object.assign(pg, { auto: false, x: Math.floor(bb[0] - m), y: Math.floor(bb[1] - m), width: Math.ceil(bb[2] - bb[0] + 2 * m), height: Math.ceil(bb[3] - bb[1] + 2 * m) });
    })]]));
    p.insertAdjacentHTML('beforeend', `<div class="sect">Tips</div><div class="sub">Drag symbols from the left, <b>W</b> for wires (they snap to pins), <b>L</b> to name a net. Wires follow parts when you move them. Double-click any text to edit it. The <b>Script</b> tab builds schematics in Python.</div>`);
    return;
  }
  if (sel.length > 1) {
    head(`${sel.length} selected`, [...new Set(sel.map((e) => e.type === 'comp' ? S.cat[e.sym]?.title : e.type))].join(', '));
    const styled = sel.filter((e) => e.type === 'comp' || e.type === 'wire' || e.type === 'arrow');
    if (styled.length) p.append(field('Style', seg(styled[0].style || '', STYLES, (v) => edit(() => { for (const e of styled) e.style = v; }))));
    p.append(btns([['Rotate', () => transformSel('rot')], ['Mirror', () => transformSel('mir')], ['To front', () => reorder(true)], ['To back', () => reorder(false)], ['Delete', del, 'danger']]));
    return;
  }
  const e = sel[0];
  if (e.type === 'comp') {
    const c = S.cat[e.sym];
    head(`${G.esc(c?.title || e.sym)} <small>${e.sym}</small>`, '');
    for (const [k, spec] of Object.entries(c?.props || {})) {
      const v = e.props?.[k] ?? spec.default;
      let input;
      if (spec.type === 'bool') input = chk(v, setp(e, k));
      else if (spec.type === 'enum') input = sel_(v, spec.choices, setp(e, k));
      else if (spec.type === 'num') input = inp(v, setp(e, k), { type: 'number', mono: true });
      else if (spec.type === 'text') {
        input = document.createElement('textarea'); input.value = v; input.rows = 3;
        input.oninput = () => setp(e, k)(input.value, true); input.onkeydown = (ev) => ev.stopPropagation();
      } else input = inp(v, setp(e, k), { mono: k !== 'ref', coalesce: true });
      const f = field(spec.label.charAt(0).toUpperCase() + spec.label.slice(1), input);
      if (spec.help) f.title = spec.help;
      p.append(f);
    }
    p.append(sect('Placement'));
    p.append(field('Position', pair(inp(e.x, set(e, 'x'), { type: 'number', mono: true }), inp(e.y, set(e, 'y'), { type: 'number', mono: true }))));
    p.append(field('Rotation', seg(e.rot || 0, [[0, '0°'], [90, '90°'], [180, '180°'], [270, '270°']], set(e, 'rot'))));
    p.append(field('Mirror', chk(e.mirror, set(e, 'mirror'))));
    p.append(field('Style', seg(e.style || '', STYLES, set(e, 'style'))));
    if (c?.geometry?.lines?.length) {
      p.append(field('Labels', chk(!e.hide_labels, (v) => edit(() => { if (v) delete e.hide_labels; else e.hide_labels = true; }))));
    }
    const pins = pinsOf(e);
    p.insertAdjacentHTML('beforeend', `<div class="sect">Pins</div><div class="pinlist">${Object.entries(pins).map(([n, q]) => `<b>${G.esc(n)}</b> ${q[0]}, ${q[1]}`).join('<br>')}</div>`);
    const b = [['Rotate', () => transformSel('rot')], ['Mirror', () => transformSel('mir')]];
    if (e.label_offset) b.push(['Reset label', () => edit(() => { delete e.label_offset; })]);
    b.push(['To front', () => reorder(true)], ['To back', () => reorder(false)], ['Delete', del, 'danger']);
    p.append(btns(b));
  } else if (e.type === 'wire' || e.type === 'arrow') {
    head(e.type === 'wire' ? 'Wire' : 'Arrow', `${e.points.length} points · double-click a segment to add a corner`);
    p.append(field('Style', seg(e.style || '', STYLES, set(e, 'style'))));
    const ta = document.createElement('textarea'); ta.value = e.points.map((q) => q.join(', ')).join('\n'); ta.rows = Math.min(8, e.points.length + 1);
    ta.onchange = () => { const pts = ta.value.split('\n').map((l) => l.split(/[,\s]+/).filter(Boolean).map(Number)).filter((q) => q.length === 2 && q.every(Number.isFinite)); if (pts.length >= 2) edit(() => { e.points = pts; }); };
    ta.onkeydown = (ev) => ev.stopPropagation();
    p.append(field('Points', ta));
    p.append(btns([['Reverse', () => edit(() => { e.points.reverse(); })], ['Delete', del, 'danger']]));
  } else if (e.type === 'text') {
    head('Text', '');
    const ta = document.createElement('textarea'); ta.value = e.text; ta.rows = 3;
    ta.oninput = () => edit(() => { e.text = ta.value; }, e.id + '.text'); ta.onkeydown = (ev) => ev.stopPropagation();
    p.append(field('Text', ta));
    p.append(field('Class', sel_(e.cls || 'lbl', Object.entries(S.info.text_classes || {}).map(([k, v]) => [k, `${v} (${k})`]), set(e, 'cls'))));
    p.append(field('Anchor', seg(e.anchor || 'start', [['start', 'Start'], ['middle', 'Middle'], ['end', 'End']], set(e, 'anchor'))));
    p.append(field('Position', pair(inp(e.x, set(e, 'x'), { type: 'number', mono: true }), inp(e.y, set(e, 'y'), { type: 'number', mono: true }))));
    p.append(btns([['Delete', del, 'danger']]));
  } else if (e.type === 'rect') {
    head('Box', 'group shading, frame or block outline');
    p.append(field('Kind', sel_(e.cls || 'grp', [['grp', 'Group shading'], ['box', 'Box'], ['accbox', 'Accent box'], ['frame', 'Frame outline']], set(e, 'cls'))));
    p.append(field('Label', inp(e.label || '', set(e, 'label'), { coalesce: true })));
    p.append(field('Position', pair(inp(e.x, set(e, 'x'), { type: 'number', mono: true }), inp(e.y, set(e, 'y'), { type: 'number', mono: true }))));
    p.append(field('Size', pair(inp(e.w, set(e, 'w'), { type: 'number', mono: true }), inp(e.h, set(e, 'h'), { type: 'number', mono: true }))));
    p.append(field('Corner', inp(e.rx ?? 4, set(e, 'rx'), { type: 'number', mono: true })));
    p.append(btns([['To front', () => reorder(true)], ['To back', () => reorder(false)], ['Delete', del, 'danger']]));
  } else if (e.type === 'raw') {
    head('Raw SVG', 'markup kept verbatim (from an imported script)');
    p.append(field('Offset', pair(inp(e.x || 0, set(e, 'x'), { type: 'number', mono: true }), inp(e.y || 0, set(e, 'y'), { type: 'number', mono: true }))));
    const ta = document.createElement('textarea'); ta.value = e.svg; ta.rows = 6;
    ta.onchange = () => edit(() => { e.svg = ta.value; }); ta.onkeydown = (ev) => ev.stopPropagation();
    p.append(field('Markup', ta));
    p.append(btns([['Delete', del, 'danger']]));
  }
}

// ---------------------------------------------------------------- netlist pane
async function refreshNetlist() {
  try {
    const r = await api.post('/api/netlist', { doc: D() });
    $('#spice').textContent = r.spice;
    $('#netwarn').innerHTML = r.warnings.map((w) => `<div class="warn">${G.esc(w)}</div>`).join('');
    const box = $('#netlist');
    box.innerHTML = '';
    const pinMap = new Map(r.pins.map(([id, pin, net]) => [`${id}.${pin}`, net]));
    for (const [net, members] of Object.entries(r.nets).sort(([a], [b]) => a.localeCompare(b, undefined, { numeric: true }))) {
      const d = document.createElement('div');
      d.className = 'net';
      d.innerHTML = `<b>${G.esc(net)}</b><span>${members.map(([ref, pin]) => `${G.esc(ref)}.${G.esc(pin)}`).join('  ')}</span>`;
      d.onclick = () => {
        $$('.net').forEach((n) => n.classList.remove('on')); d.classList.add('on');
        S.netHL = [];
        for (const e of D().elements) if (e.type === 'comp') for (const [pin, q] of Object.entries(pinsOf(e))) if (pinMap.get(`${e.id}.${pin}`) === net) S.netHL.push(q);
        renderOverlay();
      };
      box.append(d);
    }
  } catch (err) { toast(err.message, true); }
}

// ---------------------------------------------------------------- script pane
const SAMPLE = `# Build schematics in Python. Ctrl+Enter runs this; every schematic you
# create (or pass to show()) opens as a tab. Pins are reached as part['pin'].
from schematrix import Schematic

s = Schematic('RC filter and buffer', description='First-order low-pass into a follower')
vin = s.flag((60, 120), 'VIN', side='left')
r1 = s.resistor((130, 120), value='1 kΩ')
c1 = s.capacitor(anchor='1', at=(200, 120), rot=90, value='10 nF', part='C0G')
s.gnd(c1['2'])
u1 = s.opamp(anchor='inp', at=(280, 120), top='+', part='OPA210')
s.wire(vin['p'], r1['1'])
s.wire(r1['2'], u1['inp'])                     # passes over C1's pin: a junction dot appears

out = u1['out']
fb = s.wire(out, out.offset(20, 0), out.offset(20, 45), u1['inm'].offset(-14, 45 - 15), u1['inm'].offset(-14, 0), u1['inm'])
s.wire(out.offset(20, 0), out.offset(50, 0))
s.flag(out.offset(50, 0), 'VOUT', side='right')
s.note(60, 230, 'f_c = 1 / (2π · 1 kΩ · 10 nF) ≈ 15.9 kHz')

# a resistor ladder, drawn in a loop
lad = Schematic('Ladder')
top = lad.terminal((60, 40), 'I+')
prev = top['p']
for k, (r, tap) in enumerate([('10 mΩ', 't1'), ('90 mΩ', 't2'), ('900 mΩ', 't3')], 1):
    rk = lad.resistor(anchor='1', at=prev, rot=90, value=r, length=80, style='acc' if k == 3 else '')
    prev = rk['2']
    lad.wire(prev, prev.offset(60, 0))
    lad.flag(prev.offset(60, 0), tap.upper(), side='right')
print(lad.spice())
`;
async function runScript() {
  const out = $('#runout');
  out.innerHTML = '<pre>running…</pre>';
  try {
    const r = await api.post('/api/run', { code: $('#code').value, filename: $('#scriptfile').value || 'script.py' });
    showRun(r);
  } catch (err) { out.innerHTML = `<pre class="err">${G.esc(err.message)}</pre>`; }
}
function showRun(r, legacy = false) {
  const out = $('#runout');
  out.innerHTML = '';
  if (r.stdout) out.insertAdjacentHTML('beforeend', `<pre>${G.esc(r.stdout)}</pre>`);
  if (!r.ok) { out.insertAdjacentHTML('beforeend', `<pre class="err">${G.esc(r.traceback || r.error)}</pre>`); return; }
  if (!r.docs.length) { out.insertAdjacentHTML('beforeend', '<pre>no schematics were created</pre>'); return; }
  for (const { name, doc } of r.docs) {
    const existing = S.tabs.find((t) => t.fromScript === name && !t.path);
    if (existing) { pushUndoFor(existing); existing.doc = doc; existing.dirty = true; if (existing === S.cur) { render(); renderInspector(); } }
    else { const t = openTab(doc, null, false); t.fromScript = name; t.dirty = true; }
  }
  const first = S.tabs.find((t) => t.fromScript === r.docs[0].name && !t.path);
  if (first) switchTab(first);
  toast(`${r.docs.length} schematic${r.docs.length > 1 ? 's' : ''} ${legacy ? 'imported' : 'from the script'}`);
  renderTabs(); persistSoon();
}
function pushUndoFor(t) { t.undo.push(JSON.stringify(t.doc)); t.redo = []; }
async function refreshScripts(select) {
  try {
    const files = (await api.get('/api/files')).filter((f) => f.path.endsWith('.py'));
    const s = $('#scriptfile'), cur = select || s.value;
    s.innerHTML = '<option value="">(unsaved script)</option>' + files.map((f) => `<option>${G.esc(f.path)}</option>`).join('');
    s.value = files.some((f) => f.path === cur) ? cur : '';
  } catch { /* offline */ }
}

// ---------------------------------------------------------------- files
async function filesDialog() {
  let files;
  try { files = await api.get('/api/files'); } catch (err) { toast(err.message, true); return; }
  const body = document.createElement('div');
  body.className = 'files';
  if (!files.length) body.innerHTML = '<div class="sub">The workspace is empty. Saved schematics and scripts appear here.</div>';
  for (const f of files) {
    const d = document.createElement('div');
    d.className = 'file';
    const ext = f.path.split('.').pop();
    d.innerHTML = `<span class="ic">${ext.toUpperCase()}</span><span>${G.esc(f.path)}</span><span class="m">${f.modified.replace('T', ' ').slice(0, 16)}</span><button title="Delete">✕</button>`;
    d.onclick = async (ev) => {
      if (ev.target.tagName === 'BUTTON') {
        if (await confirmBox(`Delete ${f.path} from the workspace?`, 'Delete')) { await api.del('/api/files/' + encodeURI(f.path)); filesDialog(); }
        return;
      }
      closeModal();
      openWorkspaceFile(f.path);
    };
    body.append(d);
  }
  modal(`Workspace <small style="font-weight:400;color:var(--faint);font-family:var(--mono);font-size:11px">${G.esc(S.info.workspace || '')}</small>`, body);
}
async function openWorkspaceFile(path) {
  const r = await fetch('/api/files/' + encodeURI(path));
  if (!r.ok) { toast('could not open ' + path, true); return; }
  if (path.endsWith('.json')) {
    const open = S.tabs.find((t) => t.path === path);
    if (open) { switchTab(open); return; }
    const doc = await r.json();
    openTab(doc, path);
  } else if (path.endsWith('.py')) {
    $('#code').value = await r.text();
    await refreshScripts(path);
    showPane('script');
  } else if (path.endsWith('.svg')) window.open('/api/files/' + encodeURI(path), '_blank');
  persistSoon();
}
async function save(as = false) {
  const t = T();
  let path = t.path;
  if (as || !path) {
    const name = await ask('Save as (in the workspace)', path || (G.esc(tabTitle(t)).replace(/[^\w\- ]+/g, '').trim().replace(/\s+/g, '-').toLowerCase() || 'schematic') + '.json');
    if (!name) return;
    path = name.endsWith('.json') ? name : name + '.json';
  }
  try {
    await api.put('/api/files/' + encodeURI(path), JSON.stringify(t.doc, null, 1));
    t.path = path; t.dirty = false; t.fromScript = null;
    renderTabs(); persist(); toast('Saved ' + path);
  } catch (err) { toast(err.message, true); }
}

function download(blob, name) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}
const fileBase = () => (tabTitle(T()).replace(/[^\w\-]+/g, '-').replace(/^-|-$/g, '') || 'schematic');
async function exportAs(fmt) {
  try {
    if (fmt === 'json') return download(new Blob([JSON.stringify(D(), null, 1)], { type: 'application/json' }), fileBase() + '.json');
    if (fmt === 'png' && !S.info.pdf) return exportPngClient();
    const q = fmt === 'svg-plain' ? 'format=svg&fonts=false' : `format=${fmt}`;
    const b = await api.blob('/api/render?' + q, { doc: D() });
    download(b, fileBase() + '.' + (fmt === 'svg-plain' ? 'svg' : fmt === 'spice' ? 'cir' : fmt));
  } catch (err) { toast(err.message, true); }
}
async function exportPngClient() {
  const b = await api.blob('/api/render?format=svg&fonts=true', { doc: D() });
  const url = URL.createObjectURL(b), img = new Image();
  img.onload = () => {
    const c = document.createElement('canvas'); c.width = img.width * 2; c.height = img.height * 2;
    const ctx = c.getContext('2d'); ctx.scale(2, 2); ctx.drawImage(img, 0, 0);
    c.toBlob((png) => download(png, fileBase() + '.png'));
    URL.revokeObjectURL(url);
  };
  img.src = url;
}

async function importFile(file, forceLegacy) {
  const text = await file.text();
  if (file.name.endsWith('.json')) {
    try { const doc = JSON.parse(text); if (!doc.elements) throw new Error('not a Schematrix document'); openTab(doc); } catch (err) { toast(err.message, true); }
    return;
  }
  if (file.name.endsWith('.py')) {
    const legacy = forceLegacy || (/class\s+S\b/.test(text) && /def\s+svg\(/.test(text));
    if (legacy) {
      toast('Importing figures from ' + file.name + '…');
      try { showRun(await api.post('/api/import-legacy', { code: text, filename: file.name }), true); showPane('script'); } catch (err) { toast(err.message, true); }
    } else { $('#code').value = text; showPane('script'); $('#scriptfile').value = ''; }
  }
}

// ---------------------------------------------------------------- modal helpers
function modal(title, body) {
  $('#modal-title').innerHTML = title;
  const mb = $('#modal-body'); mb.innerHTML = ''; mb.append(body);
  $('#modal').hidden = false;
}
function closeModal() { $('#modal').hidden = true; svg.focus(); }
$('#modal').addEventListener('pointerdown', (ev) => { if (ev.target.id === 'modal' || ev.target.closest('[data-close]')) closeModal(); });
function ask(title, value = '') {
  return new Promise((resolve) => {
    const d = document.createElement('div');
    d.innerHTML = `<div class="askrow"><input value="${G.esc(value)}"><button class="primary">OK</button></div>`;
    const i = $('input', d);
    const done = (v) => { closeModal(); resolve(v); };
    $('button', d).onclick = () => done(i.value.trim());
    i.onkeydown = (ev) => { ev.stopPropagation(); if (ev.key === 'Enter') done(i.value.trim()); if (ev.key === 'Escape') done(null); };
    modal(G.esc(title), d);
    const obs = new MutationObserver(() => { if ($('#modal').hidden) { obs.disconnect(); resolve(null); } });
    obs.observe($('#modal'), { attributes: true });
    setTimeout(() => { i.focus(); i.select(); }, 0);
  });
}
function confirmBox(text, ok = 'OK') {
  return new Promise((resolve) => {
    const d = document.createElement('div');
    d.innerHTML = `<p style="margin:0 0 14px">${G.esc(text)}</p><div class="row" style="justify-content:flex-end"><button class="ghost">Cancel</button><button class="primary">${G.esc(ok)}</button></div>`;
    const [c, o] = $$('button', d);
    c.onclick = () => { closeModal(); resolve(false); };
    o.onclick = () => { closeModal(); resolve(true); };
    modal('Schematrix', d);
    setTimeout(() => o.focus(), 0);
  });
}
let toastTimer = 0;
function toast(msg, err = false) {
  const t = $('#toast');
  t.textContent = msg; t.className = err ? 'err' : ''; t.hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => { t.hidden = true; }, err ? 5000 : 2200);
}
function helpDialog() {
  const k = [['V', 'Select'], ['W', 'Wire'], ['L', 'Net label'], ['T', 'Text'], ['B', 'Group box'], ['A', 'Arrow'], ['/', 'Find symbol'],
    ['R', 'Rotate 90°'], ['M', 'Mirror'], ['E', 'Accent style'], ['Del', 'Delete'], ['Arrows', 'Nudge (Shift: ×4)'],
    ['Ctrl Z / Y', 'Undo / redo'], ['Ctrl C / V / D', 'Copy / paste / duplicate'], ['Ctrl S', 'Save'], ['Ctrl Enter', 'Run script'],
    ['F', 'Fit'], ['G', 'Grid'], ['Space + drag', 'Pan'], ['Alt + drag', 'Move a whole wire'], ['Wheel', 'Zoom'], ['Esc', 'Cancel / finish'], ['Dbl-click', 'Edit text / add wire corner']];
  const d = document.createElement('div'); d.className = 'keys';
  d.innerHTML = k.map(([a, b]) => `<kbd>${a}</kbd><span>${b}</span>`).join('');
  modal('Keyboard shortcuts', d);
}

// ---------------------------------------------------------------- commands, menus, keys
function showPane(name) {
  $$('.ptabs button').forEach((b) => b.classList.toggle('on', b.dataset.pane === name));
  $$('.pane').forEach((p) => { p.hidden = p.id !== 'pane-' + name; });
  if (name === 'netlist') refreshNetlist(); else { S.netHL = null; renderOverlay(); }
}
function setStyle(st) { S.style = st; $$('#stylepick button').forEach((b) => b.classList.toggle('on', b.dataset.style === st)); }
function closeMenus() { $$('.menu').forEach((m) => m.classList.remove('open')); }

const COMMANDS = {
  new: () => openTab(newDoc()), open: filesDialog, upload: () => { $('#fileinput').dataset.legacy = ''; $('#fileinput').click(); },
  'import-legacy': () => { $('#fileinput').dataset.legacy = '1'; $('#fileinput').click(); },
  save: () => save(false), saveas: () => save(true), undo, redo,
  cut: () => { if (copySel()) del(); }, copy: copySel, paste, duplicate: () => { if (copySel()) paste(); }, delete: del,
  selectall: () => { T().sel = new Set(D().elements.map((e) => e.id)); render(); renderInspector(); },
  rotate: () => transformSel('rot'), mirror: () => transformSel('mir'), accent: toggleAccent, front: () => reorder(true), back: () => reorder(false),
  fit, zoomin: () => zoomAt(1.25), zoomout: () => zoomAt(0.8), zoom100: () => zoomAt(1 / T().view.k),
  grid: () => { S.grid = !S.grid; render(); }, help: helpDialog,
  junctions: () => edit((d) => { d.page.junctions = d.page.junctions === false; }),
  hops: () => edit((d) => { d.page.hops = !d.page.hops; }),
  'export-svg': () => exportAs('svg'), 'export-svg-plain': () => exportAs('svg-plain'), 'export-png': () => exportAs('png'),
  'export-pdf': () => exportAs('pdf'), 'export-spice': () => exportAs('spice'), 'export-json': () => exportAs('json'),
  'copy-svg': async () => { try { const b = await api.blob('/api/render?format=svg&fonts=false', { doc: D() }); await navigator.clipboard.writeText(await b.text()); toast('SVG copied'); } catch (err) { toast(err.message, true); } },
};
function cmd(name) { closeMenus(); COMMANDS[name]?.(); }

document.addEventListener('click', (ev) => {
  const c = ev.target.closest('[data-cmd]');
  if (c) { cmd(c.dataset.cmd); return; }
  const m = ev.target.closest('.menu > button');
  if (m) { const open = m.parentElement.classList.contains('open'); closeMenus(); if (!open) m.parentElement.classList.add('open'); return; }
  if (!ev.target.closest('.menu')) closeMenus();
});
$$('.menu > button').forEach((b) => b.addEventListener('pointerenter', () => { if ($('.menu.open') && !b.parentElement.classList.contains('open')) { closeMenus(); b.parentElement.classList.add('open'); } }));
$$('#tools button').forEach((b) => { b.onclick = () => setTool(b.dataset.tool); });
$$('#stylepick button').forEach((b) => { b.onclick = () => setStyle(b.dataset.style); });
$$('.ptabs button').forEach((b) => { b.onclick = () => showPane(b.dataset.pane); });
$('#symsearch').addEventListener('input', (ev) => buildPalette(ev.target.value));
$('#symsearch').addEventListener('keydown', (ev) => {
  ev.stopPropagation();
  if (ev.key === 'Enter') { const first = $('#palette .sym'); first?.click(); }
  if (ev.key === 'Escape') { ev.target.value = ''; buildPalette(); svg.focus(); }
});
$('#fileinput').addEventListener('change', (ev) => { const f = ev.target.files[0]; if (f) importFile(f, ev.target.dataset.legacy === '1'); ev.target.value = ''; });
$('#netrefresh').onclick = refreshNetlist;
$('#netdl').onclick = () => exportAs('spice');
$('#runscript').onclick = runScript;
$('#savescript').onclick = async () => {
  const cur = $('#scriptfile').value;
  const name = cur || (await ask('Save script as', 'script.py'));
  if (!name) return;
  const path = name.endsWith('.py') ? name : name + '.py';
  try { await api.put('/api/files/' + encodeURI(path), $('#code').value); await refreshScripts(path); toast('Saved ' + path); } catch (err) { toast(err.message, true); }
};
$('#scriptfile').onchange = async (ev) => { if (ev.target.value) { const r = await fetch('/api/files/' + encodeURI(ev.target.value)); $('#code').value = await r.text(); } };
$('#code').addEventListener('keydown', (ev) => {
  ev.stopPropagation();
  const ta = ev.target;
  if (ev.key === 'Enter' && (ev.ctrlKey || ev.metaKey)) { ev.preventDefault(); runScript(); return; }
  if (ev.key === 'Tab') {
    ev.preventDefault();
    const { selectionStart: a, selectionEnd: b, value } = ta;
    ta.value = value.slice(0, a) + '    ' + value.slice(b); ta.selectionStart = ta.selectionEnd = a + 4;
  }
  if (ev.key === 's' && (ev.ctrlKey || ev.metaKey)) { ev.preventDefault(); $('#savescript').click(); }
});
$('#code').addEventListener('input', () => { try { localStorage.setItem('schematrix-script', $('#code').value); } catch { /* best effort */ } });
document.addEventListener('dragover', (ev) => ev.preventDefault());
document.addEventListener('drop', (ev) => { ev.preventDefault(); for (const f of ev.dataTransfer.files) importFile(f); });
window.addEventListener('beforeunload', (ev) => { persist(); if (S.tabs.some((t) => t.dirty && t.path)) { ev.preventDefault(); } });

document.addEventListener('keydown', (ev) => {
  if (!$('#modal').hidden) { if (ev.key === 'Escape') closeModal(); return; }
  const tag = document.activeElement?.tagName;
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
  const mod = ev.ctrlKey || ev.metaKey, k = ev.key;
  if (mod) {
    const map = { z: ev.shiftKey ? 'redo' : 'undo', y: 'redo', c: 'copy', x: 'cut', v: 'paste', d: 'duplicate', a: 'selectall', s: ev.shiftKey ? 'saveas' : 'save', o: 'open', n: 'new', ']': 'front', '[': 'back' };
    const c = map[k.toLowerCase()];
    if (c) { ev.preventDefault(); cmd(c); }
    return;
  }
  if (k === ' ') { S.space = true; svg.classList.add('panning'); ev.preventDefault(); return; }
  if (k === 'Escape') {
    if (S.draft) finishDraft(); else if (S.tool !== 'select') setTool('select'); else { T().sel.clear(); render(); renderInspector(); }
    return;
  }
  if (k === 'Enter' && S.draft) { finishDraft(); return; }
  if (k === 'Backspace' && S.draft) { if (S.draft.pts.length > 1) S.draft.pts.pop(); else S.draft = null; renderOverlay(); ev.preventDefault(); return; }
  if (k === 'Delete' || k === 'Backspace') { del(); ev.preventDefault(); return; }
  if (k.startsWith('Arrow')) {
    const g = (D().page.grid || 5) * (ev.shiftKey ? 4 : 1);
    nudge(k === 'ArrowLeft' ? -g : k === 'ArrowRight' ? g : 0, k === 'ArrowUp' ? -g : k === 'ArrowDown' ? g : 0);
    ev.preventDefault(); return;
  }
  const keys = { v: () => setTool('select'), w: () => setTool('wire'), t: () => setTool('text'), b: () => setTool('rect'), a: () => setTool('arrow'),
    l: () => setTool('flag'), r: () => transformSel('rot'), m: () => transformSel('mir'), e: toggleAccent, f: fit, g: () => cmd('grid'),
    '+': () => zoomAt(1.25), '=': () => zoomAt(1.25), '-': () => zoomAt(0.8), '1': () => cmd('zoom100'), '?': helpDialog,
    '/': () => { if (S.draft) { S.wireMode = S.wireMode === 'hv' ? 'vh' : 'hv'; renderOverlay(); } else { ev.preventDefault(); $('#symsearch').focus(); } } };
  const fn = keys[k] || keys[k.toLowerCase()];
  if (fn) { fn(); ev.preventDefault(); }
});
document.addEventListener('keyup', (ev) => { if (ev.key === ' ') { S.space = false; svg.classList.remove('panning'); } });

// ---------------------------------------------------------------- resizable side panels
for (const [id, side] of [['#left', 'l'], ['#right', 'r']]) {
  const h = document.createElement('div');
  h.className = 'splitter ' + side;
  $(id).append(h);
  h.addEventListener('pointerdown', (ev) => {
    h.setPointerCapture(ev.pointerId);
    const x0 = ev.clientX, w0 = $(id).getBoundingClientRect().width;
    const mv = (e) => {
      const w = Math.max(180, Math.min(760, w0 + (side === 'l' ? e.clientX - x0 : x0 - e.clientX)));
      document.documentElement.style.setProperty(side === 'l' ? '--left-w' : '--right-w', w + 'px');
    };
    const up = () => { h.removeEventListener('pointermove', mv); h.removeEventListener('pointerup', up); };
    h.addEventListener('pointermove', mv); h.addEventListener('pointerup', up);
  });
}

// ---------------------------------------------------------------- boot
async function boot() {
  try {
    [S.info, S.catList] = await Promise.all([api.get('/api/info'), api.get('/api/symbols')]);
  } catch (err) {
    document.body.innerHTML = `<p style="padding:40px;font-family:sans-serif">Schematrix could not reach its server: ${G.esc(err.message)}</p>`;
    return;
  }
  for (const e of S.catList) { S.cat[e.name] = e; S.geo.set(geoKey(e.name, {}), e.geometry); }
  const pst = document.createElement('style');           // palette thumbnails always use the light theme
  pst.textContent = scopeCss(S.info.css.instrix, '.schp');
  document.head.append(pst);
  buildPalette();
  $('#code').value = localStorage.getItem('schematrix-script') || SAMPLE;
  if (!S.info.scripts) { $('#runscript').disabled = true; $('#runscript').title = 'Script execution is disabled on this server'; }
  if (!restore()) openTab(newDoc());
  setTool('select');
  refreshScripts();
  const q = new URLSearchParams(location.search).get('open');
  if (q) openWorkspaceFile(q);
  window.schematrix = { S, api, cmd, openTab, render };   // for debugging from the console
}
boot();
