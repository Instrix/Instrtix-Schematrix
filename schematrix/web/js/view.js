// Pan/zoom, bounding boxes, and drawing the sheet, overlay and status bar.
import * as G from './geom.js';
import { D, geoOf, pinsOf, S, selected, T, undo } from './state.js';
import { draftPath, elbow } from './tools.js';
import { $, api, svg } from './util.js';

// ---------------------------------------------------------------- view
export function applyView() {
  const v = T().view;
  $('#viewport').setAttribute('transform', `translate(${v.x} ${v.y}) scale(${v.k})`);
  $('#st-zoom').textContent = Math.round(v.k * 100) + '%';
  updateGrid();
}
export function pageBox() {
  const d = D(), p = d.page;
  if (p.auto || !p.width) {
    const b = docBBox(), m = p.margin ?? 20;
    return [Math.floor(b[0] - m), Math.floor(b[1] - m), Math.ceil(b[2] - b[0] + 2 * m), Math.ceil(b[3] - b[1] + 2 * m)];
  }
  return [p.x || 0, p.y || 0, p.width, p.height];
}
export function fit() {
  const t = T(), r = svg.getBoundingClientRect();
  if (!r.width) return;
  const [x, y, w, h] = pageBox();
  const k = Math.min((r.width - 60) / w, (r.height - 60) / h, 2.5);
  t.view = { k, x: (r.width - w * k) / 2 - x * k, y: (r.height - h * k) / 2 - y * k };
  applyView();
}
export function zoomAt(f, cx, cy) {
  T().fitPending = false;
  const v = T().view, r = svg.getBoundingClientRect();
  cx ??= r.width / 2; cy ??= r.height / 2;
  const k = Math.min(12, Math.max(0.08, v.k * f));
  v.x = cx - (cx - v.x) * (k / v.k); v.y = cy - (cy - v.y) * (k / v.k); v.k = k;
  applyView();
}
export function updateGrid() {
  const g = D().page.grid || 5, k = T().view?.k || 1;
  let step = g;
  while (step * k < 9) step *= 2;
  const pat = $('#gridpat');
  pat.setAttribute('width', step); pat.setAttribute('height', step);
  pat.firstElementChild.setAttribute('r', Math.max(0.5, 0.9 / Math.sqrt(k)));
}
export function toWorld(ev) {
  const r = svg.getBoundingClientRect(), v = T().view;
  return [(ev.clientX - r.left - v.x) / v.k, (ev.clientY - r.top - v.y) / v.k];
}
export function toScreen(x, y) {
  const r = svg.getBoundingClientRect(), v = T().view;
  return [r.left + v.x + x * v.k, r.top + v.y + y * v.k];
}

// ---------------------------------------------------------------- bounding boxes
export function bboxOf(e, withLabels = true) {
  if (e.type === 'raw' && !e.bbox) {
    const bb = S.rawBB.get(e.id);
    return bb ? [bb[0], bb[1], bb[2], bb[3]] : null;
  }
  return G.elementBBox(e, S.cat, geoOf, withLabels);
}
export function docBBox() {
  const bs = D().elements.map((e) => bboxOf(e)).filter(Boolean);
  if (!bs.length) return [0, 0, 400, 300];
  return [Math.min(...bs.map((b) => b[0])), Math.min(...bs.map((b) => b[1])), Math.max(...bs.map((b) => b[2])), Math.max(...bs.map((b) => b[3]))];
}
export const union = (bs) => [Math.min(...bs.map((b) => b[0])), Math.min(...bs.map((b) => b[1])), Math.max(...bs.map((b) => b[2])), Math.max(...bs.map((b) => b[3]))];

// ---------------------------------------------------------------- rendering
export let themeCss = '';
export const scopeCss = (css, scope) => css.replace(/(^|\})\s*([^{}]+)\{/g, (m, a, sel) => `${a}\n${sel.split(',').map((x) => scope + ' ' + x.trim()).join(', ')} {`);
const ownCss = new Map();        // a document's own theme (token overrides) -> CSS from the server
export function setThemeCss() {
  const th = D().theme;
  const name = typeof th === 'string' ? th : th?.base || 'instrix';
  const tok = { ...S.info.themes?.instrix, ...(S.info.themes?.[name] || {}), ...(typeof th === 'object' ? th : {}) };
  let css = S.info.css?.[name] || S.info.css?.instrix || '';
  if (typeof th === 'object' && th) {
    const key = JSON.stringify(th);
    if (ownCss.has(key)) css = ownCss.get(key);
    else {                        // meanwhile: the base theme with its colours swapped
      for (const [k, v] of Object.entries(th)) if (String(S.info.themes?.instrix?.[k] || '').startsWith('#')) css = css.split(S.info.themes.instrix[k]).join(v);
      api.post('/api/theme-css', { theme: th }).then((r) => { ownCss.set(key, r.css); if (JSON.stringify(D().theme) === key) setThemeCss(); }).catch(() => {});
    }
  }
  css = scopeCss(css, '.sch');
  themeCss = css;
  let st = $('#themecss');
  if (!st) { st = document.createElement('style'); st.id = 'themecss'; document.head.append(st); }
  st.textContent = css;
  document.documentElement.style.setProperty('--pagefill', tok.paper || '#fff');
}

export function hitShape(e) {
  if (e.type === 'wire' || e.type === 'arrow') return `<polyline class="hit" points="${e.points.map((p) => p.join(',')).join(' ')}"/>`;
  if (e.type === 'comp' || e.type === 'text') {
    const b = bboxOf(e, false);
    if (!b) return '';
    return `<rect class="hitr" x="${b[0] - 2}" y="${b[1] - 2}" width="${b[2] - b[0] + 4}" height="${b[3] - b[1] + 4}"/>`;
  }
  return '';
}

// pointer-driven redraws are coalesced to one per animation frame (WebKitGTK, used by the desktop window on
// Linux, is noticeably slower than Chromium at replacing the sheet's markup)
let frame = 0, overlayFrame = 0;
export function renderSoon() { if (!frame) frame = requestAnimationFrame(() => { frame = 0; render(); }); }
export function overlaySoon() { if (!overlayFrame && !frame) overlayFrame = requestAnimationFrame(() => { overlayFrame = 0; renderOverlay(); }); }

export function render() {
  if (frame) { cancelAnimationFrame(frame); frame = 0; }
  if (!S.cur) return;
  setThemeCss();
  const d = D();
  let html = '';
  const hops = d.page.hops ? G.hops(d, geoOf) : {};
  for (const e of d.elements) {
    html += e.locked ? `<g class="el locked">${G.elementSvg(e, S.cat, geoOf, hops[e.id])}</g>`
      : `<g class="el" data-id="${e.id}">${hitShape(e)}${G.elementSvg(e, S.cat, geoOf, hops[e.id])}</g>`;
  }
  if (d.page.junctions !== false) {
    const manual = new Set(d.elements.filter((e) => e.type === 'comp' && e.sym === 'dot').map((e) => G.key([e.x, e.y])));
    for (const p of G.junctions(d, geoOf)) if (!manual.has(G.key(p))) html += `<circle class="dot jn" cx="${p[0]}" cy="${p[1]}" r="3"/>`;
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

export function renderOverlay() {
  if (overlayFrame) { cancelAnimationFrame(overlayFrame); overlayFrame = 0; }
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

export function renderStatus() {
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
