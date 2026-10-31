// The symbol editor: draw a symbol from lines, shapes, text and pins, and save it to the workspace library.
// A symbol is the same JSON the built-in library produces (schematrix/symbols/custom.py): prims, pins, label.
import * as G from './geom.js';
import { buildPalette } from './palette.js';
import { D, edit, geoKey, S } from './state.js';
import { confirmBox, toast } from './ui.js';
import { $, api, clone } from './util.js';
import { render } from './view.js';

const TOOLS = [['select', 'Select', 'V'], ['line', 'Line', 'L'], ['poly', 'Shape', 'G'], ['rect', 'Rectangle', 'R'],
  ['circle', 'Circle', 'C'], ['text', 'Text', 'T'], ['pin', 'Pin', 'P']];
const STROKES = [['w', 'Normal'], ['w plate', 'Heavy'], ['w thin', 'Thin'], ['w para', 'Dashed']];
const FILLS = [['w', 'None'], ['amp', 'Paper'], ['box', 'Surface'], ['dot', 'Ink']];
const TEXTS = [['valsm', 'Small'], ['lbl', 'Label'], ['ref', 'Bold'], ['pin', 'Sign'], ['val', 'Value']];

let ed = null;            // { def, tool, sel, view, draft, drag, undo, redo, from, grid, el }

const blank = () => ({ name: '', title: 'New symbol', category: 'Custom', prefix: 'U', help: '', spice: '', fields: [],
  prims: [], pins: {}, label: { x: 0, y: -26, nx: 0, ny: -1 } });

// ---------------------------------------------------------------- entry points
export async function openSymbolEditor(opts = {}) {
  let def = blank(), from = null;
  try {
    if (opts.edit) def = clone(S.cat[opts.edit].custom);
    else if (opts.copy) { def = await api.get(`/api/symbols/copy/${encodeURIComponent(opts.copy)}?props=${encodeURIComponent(JSON.stringify(opts.props || {}))}`); from = opts.comp || null; }
  } catch (err) { toast(err.message, true); return; }
  def.fields = def.fields || []; def.spice = def.spice || '';
  ed = { def, tool: 'select', sel: null, view: { k: 3, x: 0, y: 0 }, draft: null, drag: null, undo: [], redo: [], from, grid: 5,
    existing: !!opts.edit, el: null };
  build();
}

// ---------------------------------------------------------------- layout
function build() {
  document.getElementById('symedit')?.remove();
  const el = document.createElement('div');
  el.id = 'symedit';
  el.innerHTML = `
    <header><b>Symbol editor</b><span class="sub"></span><span class="grow"></span>
      <label>Start from <select class="from"><option value="">built-in symbol…</option></select></label>
      <button data-a="save" class="primary">Save to library</button><button data-a="saveas">Save as…</button>
      <button data-a="delete" class="danger">Delete</button><button data-a="close">Close</button></header>
    <nav class="tools">${TOOLS.map(([t, n, k]) => `<button data-tool="${t}" title="${n} (${k})">${n}<small>${k}</small></button>`).join('')}
      <hr><label class="gridpick">Grid <select><option>5</option><option>2.5</option><option>1</option></select></label>
      <p class="sub">Drag to move; drag a corner handle to reshape. Double-click or Enter ends a line. Right-drag pans, wheel zooms.
      Pins are the connection points: put them on the ends of the leads.</p></nav>
    <svg class="canvas" tabindex="0"><defs><pattern id="sg" width="5" height="5" patternUnits="userSpaceOnUse">
      <circle cx="0" cy="0" r="0.35" fill="var(--faint)"/></pattern></defs><g class="vp"><rect class="gridbg" x="-400" y="-400" width="800" height="800" fill="url(#sg)"/>
      <line class="axis" x1="-400" y1="0" x2="400" y2="0"/><line class="axis" x1="0" y1="-400" x2="0" y2="400"/>
      <g class="sch art"></g><g class="ov"></g></g></svg>
    <aside class="props"></aside>`;
  document.body.append(el);
  ed.el = el;
  const sel = el.querySelector('.from');
  for (const e of S.catList) if (!e.custom) sel.append(new Option(`${e.category} · ${e.title}`, e.name));
  sel.onchange = async () => {
    if (!sel.value) return;
    if (ed.def.prims.length && !(await confirmBox('Replace the current drawing with a copy of this symbol?', 'Replace'))) { sel.value = ''; return; }
    const name = ed.def.name;
    snapshot(); ed.def = { ...(await api.get(`/api/symbols/copy/${sel.value}`)), name: name || ed.def.name };
    ed.def.spice = ed.def.spice || ''; sel.value = ''; ed.sel = null; draw(); props();
  };
  el.querySelectorAll('[data-tool]').forEach((b) => { b.onclick = () => setTool(b.dataset.tool); });
  el.querySelector('.gridpick select').onchange = (ev) => { ed.grid = Number(ev.target.value); };
  el.querySelector('[data-a=close]').onclick = close;
  el.querySelector('[data-a=save]').onclick = () => save(false);
  el.querySelector('[data-a=saveas]').onclick = () => save(true);
  el.querySelector('[data-a=delete]').onclick = remove;
  el.querySelector('[data-a=delete]').hidden = !ed.existing;
  const svg = el.querySelector('.canvas');
  svg.addEventListener('pointerdown', down); svg.addEventListener('pointermove', move); svg.addEventListener('pointerup', up);
  svg.addEventListener('dblclick', () => finishDraft());
  svg.addEventListener('contextmenu', (ev) => ev.preventDefault());
  svg.addEventListener('wheel', (ev) => { ev.preventDefault(); zoom(Math.exp(-ev.deltaY * 0.0015), ev); }, { passive: false });
  el.addEventListener('keydown', key);
  fit(); setTool('select'); props();
  svg.focus();
}

function close() { ed?.el.remove(); ed = null; }

// ---------------------------------------------------------------- view
function fit() {
  const svg = ed.el.querySelector('.canvas'), r = svg.getBoundingClientRect();
  const b = bbox() || [-40, -40, 40, 40], w = Math.max(60, b[2] - b[0]), h = Math.max(60, b[3] - b[1]);
  ed.view.k = bbox() ? Math.min(8, Math.max(1.5, Math.min(r.width / (w + 60), r.height / (h + 60)))) : 4;   // empty: a part-sized view
  ed.view.x = r.width / 2 - ((b[0] + b[2]) / 2) * ed.view.k; ed.view.y = r.height / 2 - ((b[1] + b[3]) / 2) * ed.view.k;
  applyView();
}
function applyView() { ed.el.querySelector('.vp').setAttribute('transform', `translate(${ed.view.x} ${ed.view.y}) scale(${ed.view.k})`); }
function zoom(f, ev) {
  const r = ed.el.querySelector('.canvas').getBoundingClientRect(), cx = ev.clientX - r.left, cy = ev.clientY - r.top, v = ed.view;
  const k = Math.min(20, Math.max(0.5, v.k * f));
  v.x = cx - (cx - v.x) * (k / v.k); v.y = cy - (cy - v.y) * (k / v.k); v.k = k; applyView();
}
function world(ev) {
  const r = ed.el.querySelector('.canvas').getBoundingClientRect();
  return [(ev.clientX - r.left - ed.view.x) / ed.view.k, (ev.clientY - r.top - ed.view.y) / ed.view.k];
}
const snap = (v) => Math.round(v / ed.grid) * ed.grid;
const snapP = (w) => [snap(w[0]), snap(w[1])];

function bbox() {
  const xs = [], ys = [];
  for (const p of ed.def.prims) for (const [x, y] of points(p)) { xs.push(x); ys.push(y); }
  for (const [x, y] of Object.values(ed.def.pins)) { xs.push(x); ys.push(y); }
  return xs.length ? [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)] : null;
}
function points(p) {
  if (p.k === 'pl' || p.k === 'pg') return p.pts;
  if (p.k === 'rc') return [[p.x, p.y], [p.x + p.w, p.y + p.h]];
  if (p.k === 'ci') return [[p.x - p.r, p.y - p.r], [p.x + p.r, p.y + p.r]];
  const w = G.textWidth(p.s, p.c), x0 = p.x - (p.a === 'middle' ? w / 2 : p.a === 'end' ? w : 0);
  return [[x0, p.y - 10], [x0 + w, p.y + 3]];
}

// ---------------------------------------------------------------- drawing
function draw() {
  const art = ed.el.querySelector('.art'), ov = ed.el.querySelector('.ov'), k = ed.view.k;
  art.innerHTML = ed.def.prims.map((p, i) => `<g data-i="${i}">${hit(p)}${G.primSvg(p, null, '')}</g>`).join('');
  let o = '';
  for (const [n, [x, y]] of Object.entries(ed.def.pins)) {
    const on = ed.sel?.pin === n;
    o += `<g data-pin="${G.esc(n)}"><circle class="sepin${on ? ' on' : ''}" cx="${x}" cy="${y}" r="${3.5 / k * 2}"/>`
      + `<text class="sepinname" x="${x + 4}" y="${y - 4}" style="font-size:${11 / k * 2}px">${G.esc(n)}</text></g>`;
  }
  const L = ed.def.label;
  o += `<g data-label="1"><text class="selabel${ed.sel?.label ? ' on' : ''}" x="${L.x}" y="${L.y}" text-anchor="${L.nx > 0 ? 'start' : L.nx < 0 ? 'end' : 'middle'}"
    style="font-size:${10 / k * 2}px">REF / value</text></g>`;
  if (Number.isInteger(ed.sel?.i)) {
    const p = ed.def.prims[ed.sel.i];
    if (p) {
      const pts = points(p), xs = pts.map((q) => q[0]), ys = pts.map((q) => q[1]);
      o += `<rect class="selbox" x="${Math.min(...xs) - 2}" y="${Math.min(...ys) - 2}" width="${Math.max(...xs) - Math.min(...xs) + 4}" height="${Math.max(...ys) - Math.min(...ys) + 4}"/>`;
      handles(p).forEach(([x, y], j) => { o += `<circle class="vh" data-h="${j}" cx="${x}" cy="${y}" r="${4 / k}"/>`; });
    }
  }
  if (ed.draft) {
    const d = ed.draft;
    if (d.kind === 'line' || d.kind === 'poly') o += `<polyline class="sedraft" points="${[...d.pts, d.cur].map((q) => q.join(',')).join(' ')}"/>`;
    if (d.kind === 'rect') o += `<rect class="sedraft" x="${Math.min(d.a[0], d.cur[0])}" y="${Math.min(d.a[1], d.cur[1])}" width="${Math.abs(d.cur[0] - d.a[0])}" height="${Math.abs(d.cur[1] - d.a[1])}"/>`;
    if (d.kind === 'circle') o += `<circle class="sedraft" cx="${d.a[0]}" cy="${d.a[1]}" r="${Math.hypot(d.cur[0] - d.a[0], d.cur[1] - d.a[1])}"/>`;
  }
  ov.innerHTML = o;
  ed.el.querySelector('header .sub').textContent = `${ed.def.title || 'untitled'} · ${ed.def.prims.length} shapes · ${Object.keys(ed.def.pins).length} pins`;
}
function hit(p) {
  if (p.k === 'pl' || p.k === 'pg') return `<polyline class="sehit" points="${p.pts.map((q) => q.join(',')).join(' ')}${p.k === 'pg' ? ' ' + p.pts[0].join(',') : ''}"/>`;
  const pts = points(p), xs = pts.map((q) => q[0]), ys = pts.map((q) => q[1]);
  return `<rect class="sehitr" x="${Math.min(...xs) - 2}" y="${Math.min(...ys) - 2}" width="${Math.max(...xs) - Math.min(...xs) + 4}" height="${Math.max(...ys) - Math.min(...ys) + 4}"/>`;
}
function handles(p) {
  if (p.k === 'pl' || p.k === 'pg') return p.pts;
  if (p.k === 'rc') return [[p.x + p.w, p.y + p.h]];
  if (p.k === 'ci') return [[p.x + p.r, p.y]];
  return [];
}

// ---------------------------------------------------------------- editing
function snapshot() { ed.undo.push(JSON.stringify(ed.def)); ed.redo = []; if (ed.undo.length > 200) ed.undo.shift(); }
function undo() { if (!ed.undo.length) return; ed.redo.push(JSON.stringify(ed.def)); ed.def = JSON.parse(ed.undo.pop()); ed.sel = null; draw(); props(); }
function redo() { if (!ed.redo.length) return; ed.undo.push(JSON.stringify(ed.def)); ed.def = JSON.parse(ed.redo.pop()); ed.sel = null; draw(); props(); }

function setTool(t) {
  finishDraft();
  ed.tool = t;
  ed.el.querySelectorAll('[data-tool]').forEach((b) => b.classList.toggle('on', b.dataset.tool === t));
  ed.el.querySelector('.canvas').dataset.tool = t;
}

function down(ev) {
  const w = world(ev), p = snapP(w);
  ed.el.querySelector('.canvas').focus();
  if (ev.button === 2 || ev.button === 1) { ed.drag = { kind: 'pan', sx: ev.clientX, sy: ev.clientY, vx: ed.view.x, vy: ed.view.y }; return; }
  if (ev.button !== 0) return;
  ev.currentTarget.setPointerCapture(ev.pointerId);
  const t = ed.tool;
  if (t === 'line' || t === 'poly') {
    if (!ed.draft) ed.draft = { kind: t, pts: [p], cur: p };
    else if (G.key(ed.draft.pts.at(-1)) !== G.key(p)) ed.draft.pts.push(p);
    draw(); return;
  }
  if (t === 'rect' || t === 'circle') { ed.draft = { kind: t, a: p, cur: p }; draw(); return; }
  if (t === 'text') {
    snapshot(); ed.def.prims.push({ k: 'tx', x: p[0], y: p[1], s: 'Text', c: 'valsm', a: 'middle', ctr: true });
    ed.sel = { i: ed.def.prims.length - 1 }; setTool('select'); draw(); props();
    setTimeout(() => ed.el.querySelector('.props [name=text]')?.select(), 0); return;
  }
  if (t === 'pin') {
    snapshot(); let n = Object.keys(ed.def.pins).length + 1;
    while (`${n}` in ed.def.pins) n++;
    ed.def.pins[`${n}`] = p; ed.sel = { pin: `${n}` }; draw(); props(); return;
  }
  // select tool
  const h = ev.target.closest('[data-h]'), pin = ev.target.closest('[data-pin]'), lab = ev.target.closest('[data-label]');
  const prim = ev.target.closest('[data-i]');
  if (h && Number.isInteger(ed.sel?.i)) { snapshot(); ed.drag = { kind: 'handle', j: +h.dataset.h }; return; }
  if (pin) ed.sel = { pin: pin.dataset.pin };
  else if (lab) ed.sel = { label: true };
  else if (prim) ed.sel = { i: +prim.dataset.i };
  else { ed.sel = null; draw(); props(); return; }
  snapshot();
  ed.drag = { kind: 'move', start: p, orig: clone(ed.def), moved: false };
  draw(); props();
}

function move(ev) {
  const dr = ed?.drag;
  if (dr?.kind === 'pan') { ed.view.x = dr.vx + ev.clientX - dr.sx; ed.view.y = dr.vy + ev.clientY - dr.sy; applyView(); return; }
  const p = snapP(world(ev));
  if (ed?.draft) { ed.draft.cur = p; draw(); return; }
  if (!dr) return;
  if (dr.kind === 'move') {
    const dx = p[0] - dr.start[0], dy = p[1] - dr.start[1];
    if (!dx && !dy && !dr.moved) return;
    dr.moved = true;
    const o = dr.orig, s = ed.sel;
    if (s.pin) { const q = o.pins[s.pin]; ed.def.pins[s.pin] = [q[0] + dx, q[1] + dy]; }
    else if (s.label) { ed.def.label = { ...o.label, x: o.label.x + dx, y: o.label.y + dy }; }
    else ed.def.prims[s.i] = shift(o.prims[s.i], dx, dy);
    draw();
  } else if (dr.kind === 'handle') {
    const q = ed.def.prims[ed.sel.i];
    if (q.k === 'pl' || q.k === 'pg') q.pts[dr.j] = p;
    else if (q.k === 'rc') { q.w = p[0] - q.x; q.h = p[1] - q.y; }
    else if (q.k === 'ci') q.r = Math.max(0.5, Math.hypot(p[0] - q.x, p[1] - q.y));
    draw();
  }
}
function shift(p, dx, dy) {
  const q = clone(p);
  if (q.pts) q.pts = q.pts.map(([x, y]) => [x + dx, y + dy]); else { q.x += dx; q.y += dy; }
  return q;
}
function up() {
  const dr = ed?.drag;
  if (!dr) {
    const d = ed?.draft;
    if (d && (d.kind === 'rect' || d.kind === 'circle')) {
      const [a, c] = [d.a, d.cur];
      if (d.kind === 'rect' && Math.abs(c[0] - a[0]) > 0 && Math.abs(c[1] - a[1]) > 0) {
        snapshot(); ed.def.prims.push({ k: 'rc', x: Math.min(a[0], c[0]), y: Math.min(a[1], c[1]), w: Math.abs(c[0] - a[0]), h: Math.abs(c[1] - a[1]), c: 'w', rx: 0 });
      } else if (d.kind === 'circle' && Math.hypot(c[0] - a[0], c[1] - a[1]) > 0) {
        snapshot(); ed.def.prims.push({ k: 'ci', x: a[0], y: a[1], r: Math.round(Math.hypot(c[0] - a[0], c[1] - a[1]) * 2) / 2, c: 'w' });
      }
      ed.draft = null; ed.sel = { i: ed.def.prims.length - 1 }; draw(); props();
    }
    return;
  }
  ed.drag = null;
  if (dr.kind === 'move' && !dr.moved) ed.undo.pop();        // a click, not a change
  if (dr.kind === 'handle') {
    const q = ed.def.prims[ed.sel.i];
    if (q.k === 'rc') { if (q.w < 0) { q.x += q.w; q.w = -q.w; } if (q.h < 0) { q.y += q.h; q.h = -q.h; } }
  }
  draw(); props();
}
function finishDraft() {
  const d = ed?.draft;
  if (!d) return;
  ed.draft = null;
  if ((d.kind === 'line' || d.kind === 'poly') && d.pts.length >= 2) {
    snapshot();
    ed.def.prims.push(d.kind === 'poly' && d.pts.length >= 3 ? { k: 'pg', pts: d.pts, c: 'amp' } : { k: 'pl', pts: d.pts, c: 'w' });
    ed.sel = { i: ed.def.prims.length - 1 };
  }
  draw(); props();
}

function key(ev) {
  ev.stopPropagation();
  const tag = document.activeElement?.tagName;
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') { if (ev.key === 'Escape') ed.el.querySelector('.canvas').focus(); return; }
  const mod = ev.ctrlKey || ev.metaKey, k = ev.key.toLowerCase();
  if (mod && k === 'z') { ev.preventDefault(); if (ev.shiftKey) redo(); else undo(); return; }
  if (mod && k === 'y') { ev.preventDefault(); redo(); return; }
  if (mod && k === 's') { ev.preventDefault(); save(false); return; }
  if (mod && k === 'd' && Number.isInteger(ed.sel?.i)) {
    ev.preventDefault(); snapshot(); ed.def.prims.push(shift(ed.def.prims[ed.sel.i], ed.grid * 2, ed.grid * 2)); ed.sel = { i: ed.def.prims.length - 1 }; draw(); props(); return;
  }
  if (ev.key === 'Escape') { if (ed.draft) { ed.draft = null; draw(); } else if (ed.tool !== 'select') setTool('select'); else { ed.sel = null; draw(); props(); } return; }
  if (ev.key === 'Enter') { finishDraft(); return; }
  if (ev.key === 'Delete' || ev.key === 'Backspace') {
    ev.preventDefault();
    if (ed.draft?.pts?.length > 1) { ed.draft.pts.pop(); draw(); return; }
    if (!ed.sel || ed.sel.label) return;
    snapshot();
    if (ed.sel.pin) delete ed.def.pins[ed.sel.pin]; else ed.def.prims.splice(ed.sel.i, 1);
    ed.sel = null; draw(); props(); return;
  }
  if (ev.key.startsWith('Arrow') && ed.sel) {
    ev.preventDefault();
    const g = ed.grid * (ev.shiftKey ? 4 : 1), dx = ev.key === 'ArrowLeft' ? -g : ev.key === 'ArrowRight' ? g : 0, dy = ev.key === 'ArrowUp' ? -g : ev.key === 'ArrowDown' ? g : 0;
    snapshot();
    if (ed.sel.pin) { const q = ed.def.pins[ed.sel.pin]; ed.def.pins[ed.sel.pin] = [q[0] + dx, q[1] + dy]; }
    else if (ed.sel.label) { ed.def.label.x += dx; ed.def.label.y += dy; } else ed.def.prims[ed.sel.i] = shift(ed.def.prims[ed.sel.i], dx, dy);
    draw(); return;
  }
  if (k === 'f') { fit(); return; }
  const t = TOOLS.find((x) => x[2].toLowerCase() === k);
  if (t && !mod) setTool(t[0]);
}

// ---------------------------------------------------------------- properties panel
function row(label, input) { const d = document.createElement('label'); d.className = 'f'; d.append(label, input); return d; }
function inputOf(value, on, opts = {}) {
  const i = document.createElement(opts.area ? 'textarea' : 'input');
  if (opts.type) i.type = opts.type; i.value = value ?? ''; if (opts.name) i.name = opts.name; if (opts.placeholder) i.placeholder = opts.placeholder;
  i.onchange = () => { snapshot(); on(opts.type === 'number' ? Number(i.value) : i.value); draw(); };
  return i;
}
function selectOf(value, options, on) {
  const s = document.createElement('select');
  for (const [v, t] of options) s.append(new Option(t, v));
  s.value = value; s.onchange = () => { snapshot(); on(s.value); draw(); props(); };
  return s;
}
function props() {
  const p = ed.el.querySelector('.props'), d = ed.def;
  p.innerHTML = '<h4>Symbol</h4>';
  p.append(row('Name (id)', inputOf(d.name, (v) => { d.name = v.trim().toLowerCase().replace(/[^a-z0-9_]/g, '_'); props(); }, { placeholder: 'e.g. ldo_3v3' })));
  p.append(row('Title', inputOf(d.title, (v) => { d.title = v; })));
  p.append(row('Category', inputOf(d.category, (v) => { d.category = v || 'Custom'; })));
  p.append(row('Reference prefix', inputOf(d.prefix, (v) => { d.prefix = v.toUpperCase(); })));
  p.append(row('Description', inputOf(d.help, (v) => { d.help = v; })));
  p.append(row('Suggested fields', inputOf(d.fields.join(', '), (v) => { d.fields = v.split(',').map((x) => x.trim()).filter(Boolean); }, { placeholder: 'Voltage, Tolerance' })));
  p.append(row('SPICE line', inputOf(d.spice, (v) => { d.spice = v; }, { placeholder: 'X {IN} {GND} {OUT} {model}' })));
  const lab = document.createElement('div'); lab.className = 'btns';
  lab.innerHTML = '<span class="sub">Label block:</span>';
  for (const [n, t] of [['above', 'Above'], ['below', 'Below'], ['left', 'Left'], ['right', 'Right']]) {
    const b = document.createElement('button'); b.textContent = t; b.onclick = () => { snapshot(); placeLabel(n); draw(); }; lab.append(b);
  }
  p.append(lab);
  const s = ed.sel;
  if (s?.pin) {
    p.insertAdjacentHTML('beforeend', '<h4>Pin</h4>');
    p.append(row('Name', inputOf(s.pin, (v) => {
      v = v.trim(); if (!v || v === s.pin || v in d.pins) return;
      d.pins = Object.fromEntries(Object.entries(d.pins).map(([k, q]) => [k === s.pin ? v : k, q])); ed.sel = { pin: v }; props();
    }, { name: 'pinname' })));
    const [x, y] = d.pins[s.pin];
    p.append(row('Position', inputOf(`${x}, ${y}`, (v) => { const q = v.split(/[,\s]+/).map(Number); if (q.length === 2 && q.every(Number.isFinite)) d.pins[s.pin] = q; })));
  } else if (Number.isInteger(s?.i) && d.prims[s.i]) {
    const q = d.prims[s.i];
    p.insertAdjacentHTML('beforeend', `<h4>${{ pl: 'Line', pg: 'Shape', rc: 'Rectangle', ci: 'Circle', tx: 'Text' }[q.k]}</h4>`);
    if (q.k === 'tx') {
      p.append(row('Text', inputOf(q.s, (v) => { q.s = v; }, { name: 'text' })));
      p.append(row('Style', selectOf(q.c, TEXTS, (v) => { q.c = v; })));
      p.append(row('Anchor', selectOf(q.a, [['start', 'Start'], ['middle', 'Middle'], ['end', 'End']], (v) => { q.a = v; })));
      p.append(row('Centred on the point', selectOf(q.ctr ? '1' : '', [['1', 'Yes'], ['', 'No (baseline)']], (v) => { q.ctr = !!v; })));
    } else if (q.k === 'pl') {
      p.append(row('Stroke', selectOf(q.c, STROKES, (v) => { q.c = v; })));
      p.append(row('Closed', selectOf('', [['', 'No'], ['1', 'Close into a shape']], () => { q.k = 'pg'; q.c = 'amp'; })));
    } else {
      p.append(row('Fill', selectOf(FILLS.some((f) => f[0] === q.c) ? q.c : 'w', FILLS, (v) => { q.c = v; })));
      if (q.k === 'pg') p.append(row('Open', selectOf('', [['', 'No'], ['1', 'Make it a line']], () => { q.k = 'pl'; q.c = 'w'; })));
      if (q.k === 'rc') p.append(row('Corner radius', inputOf(q.rx || 0, (v) => { q.rx = v; }, { type: 'number' })));
    }
    const b = document.createElement('div'); b.className = 'btns';
    for (const [t, fn] of [['To front', () => { const [x] = d.prims.splice(s.i, 1); d.prims.push(x); ed.sel = { i: d.prims.length - 1 }; }],
      ['To back', () => { const [x] = d.prims.splice(s.i, 1); d.prims.unshift(x); ed.sel = { i: 0 }; }],
      ['Delete', () => { d.prims.splice(s.i, 1); ed.sel = null; }]]) {
      const bt = document.createElement('button'); bt.textContent = t; bt.onclick = () => { snapshot(); fn(); draw(); props(); }; b.append(bt);
    }
    p.append(b);
  }
  p.querySelectorAll('input, textarea, select').forEach((i) => { i.addEventListener('keydown', (ev) => { if (ev.key === 'Enter' && i.tagName === 'INPUT') i.blur(); }); });
}
function placeLabel(where) {
  const b = bbox() || [0, 0, 0, 0], cx = (b[0] + b[2]) / 2, cy = (b[1] + b[3]) / 2;
  ed.def.label = { above: { x: cx, y: b[1] - 6, nx: 0, ny: -1 }, below: { x: cx, y: b[3] + 4, nx: 0, ny: 1 },
    left: { x: b[0] - 6, y: cy, nx: -1, ny: 0 }, right: { x: b[2] + 6, y: cy, nx: 1, ny: 0 } }[where];
}

// ---------------------------------------------------------------- saving
async function save(asNew) {
  finishDraft();
  const d = ed.def;
  if (asNew || !d.name) {
    const name = prompt('Symbol name (lower-case letters, digits, _):', d.name ? `${d.name}_2` : '');
    if (!name) return;
    d.name = name.trim().toLowerCase().replace(/[^a-z0-9_]/g, '_');
  }
  try {
    const entry = await api.req('PUT', `/api/symbols/custom/${encodeURIComponent(d.name)}`, d).then((r) => r.json());
    await refreshCatalog(entry.name);
    ed.existing = true; ed.el.querySelector('[data-a=delete]').hidden = false;
    if (ed.from) {                                          // started from a part on the sheet: switch it over
      const comp = D().elements.find((e) => e.id === ed.from);
      if (comp) edit(() => { comp.props = Object.fromEntries(Object.entries(comp.props || {}).filter(([k]) => ['ref', 'value', 'part'].includes(k))); comp.sym = entry.name; });
      ed.from = null;
    }
    toast(`Saved ${entry.title} to the library (Custom)`);
  } catch (err) { toast(err.message, true); }
}
async function remove() {
  const name = ed.def.name;
  if (!(await confirmBox(`Delete the symbol "${name}" from the library? Sheets that use it keep their own copy.`, 'Delete'))) return;
  try { await api.del(`/api/symbols/custom/${encodeURIComponent(name)}`); await refreshCatalog(null); close(); toast('Deleted ' + name); } catch (err) { toast(err.message, true); }
}

// reload the catalogue after a change and drop cached geometry of the changed symbol
export async function refreshCatalog(changed) {
  S.catList = await api.get('/api/symbols');
  S.cat = {};
  for (const k of [...S.geo.keys()]) if (!changed || k === changed || k.startsWith(changed + '|')) S.geo.delete(k);
  for (const e of S.catList) {
    S.cat[e.name] = e; S.geo.set(geoKey(e.name, {}), e.geometry);
    for (const p of e.presets || []) S.geo.set(geoKey(e.name, p.props), p.geometry);
  }
  buildPalette($('#symsearch').value);
  render();
}

// the inspector's button for a selected part: edit it (custom) or start a custom copy of it (built-in)
export function symbolButton(e) {
  const c = S.cat[e.sym];
  if (!c || S.info.public) return null;
  return c.custom ? ['Edit symbol…', () => openSymbolEditor({ edit: e.sym })]
    : ['Customise symbol…', () => openSymbolEditor({ copy: e.sym, props: e.props, comp: e.id })];
}

// symbols a document carries but this library lacks (a sheet from someone else): register them for this session
export async function adoptEmbedded(doc) {
  const missing = Object.fromEntries(Object.entries(doc?.symbols || {}).filter(([n]) => !S.cat[n]));
  if (!Object.keys(missing).length) return;
  try { await api.post('/api/symbols/embedded', { symbols: missing }); await refreshCatalog(null); } catch (err) { toast(err.message, true); }
}

// the custom symbols a document uses, to store inside it
export function embeddedSymbols(doc) {
  const out = {};
  for (const e of doc.elements) if (e.type === 'comp' && S.cat[e.sym]?.custom) out[e.sym] = S.cat[e.sym].custom;
  return out;
}
