// Operations on the selection: transform, delete, nudge, z-order, clipboard.
import * as G from './geom.js';
import { setStyle } from './commands.js';
import { renderInspector } from './inspector.js';
import { byId, D, edit, nextId, nextRef, pinsOf, S, selected, T } from './state.js';
import { rubber, simplify, updateGhost } from './tools.js';
import { toast } from './ui.js';
import { $, clone, snapTo } from './util.js';
import { bboxOf, union } from './view.js';

// ---------------------------------------------------------------- selection operations
export function selCenter() {
  const bs = selected().map((e) => bboxOf(e, false)).filter(Boolean);
  const b = union(bs), g = D().page.grid || 5;
  return [snapTo((b[0] + b[2]) / 2, g), snapTo((b[1] + b[3]) / 2, g)];
}
export function transformSel(kind) {
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
export function toggleAccent() {
  const sel = selected().filter((e) => e.type === 'comp' || e.type === 'wire' || e.type === 'arrow');
  if (!sel.length) { setStyle(S.style === 'acc' ? '' : 'acc'); return; }
  const on = !sel.every((e) => (e.style || '').split(' ').includes('acc'));
  edit(() => { for (const e of sel) { const t = (e.style || '').split(' ').filter((s) => s && s !== 'acc'); if (on) t.push('acc'); e.style = t.join(' '); } });
}
export function del() {
  const t = T();
  if (!t.sel.size) return;
  edit((d) => { d.elements = d.elements.filter((e) => !t.sel.has(e.id)); });
  t.sel.clear(); renderInspector();
}
export function nudge(dx, dy) {
  if (!T().sel.size) return;
  edit(() => {
    for (const e of selected()) { if ('x' in e) { e.x += dx; e.y += dy; } if (e.points) e.points = e.points.map(([x, y]) => [x + dx, y + dy]); }
  }, 'nudge');
}
// one step up or down the drawing order: each selected element swaps with its unselected neighbour
export function step(dir) {
  const t = T();
  edit((d) => {
    const E = d.elements, idx = E.map((e, i) => (t.sel.has(e.id) ? i : -1)).filter((i) => i >= 0);
    if (dir > 0) { for (const i of idx.reverse()) if (i + 1 < E.length && !t.sel.has(E[i + 1].id)) [E[i], E[i + 1]] = [E[i + 1], E[i]]; }
    else for (const i of idx) if (i > 0 && !t.sel.has(E[i - 1].id)) [E[i - 1], E[i]] = [E[i], E[i - 1]];
  });
}
export function reorder(front) {
  const t = T();
  edit((d) => {
    const s = d.elements.filter((e) => t.sel.has(e.id)), r = d.elements.filter((e) => !t.sel.has(e.id));
    d.elements = front ? [...r, ...s] : [...s, ...r];
  });
}

// clipboard: element JSON, also on the system clipboard so it pastes across tabs and windows
export function copySel() {
  const els = selected();
  if (!els.length) return false;
  const text = JSON.stringify({ schematrix: 1, elements: els });
  S.clip = text;
  navigator.clipboard?.writeText(text).catch(() => {});
  return true;
}
export async function paste() {
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

// ---------------------------------------------------------------- align and distribute
// parts, texts and boxes move by their own deltas; wires attached to moved parts stretch, like when dragging
export function moveEach(deltas) {
  edit((d) => {
    const pins = new Map();
    for (const [id, dd] of deltas) { const e = byId(id); if (e?.type === 'comp') for (const p of Object.values(pinsOf(e))) pins.set(G.key(p), dd); }
    for (const w of d.elements) {
      if (w.type !== 'wire' || deltas.has(w.id) || w.points.length < 2) continue;
      const n = w.points.length, d0 = pins.get(G.key(w.points[0])), d1 = pins.get(G.key(w.points[n - 1]));
      if (!d0 && !d1) continue;
      if (d0 && d1 && d0[0] === d1[0] && d0[1] === d1[1]) w.points = rubber({ orig: w.points, a0: true, a1: true }, d0[0], d0[1]);
      else {
        if (d0) w.points = rubber({ orig: clone(w.points), a0: true, a1: false }, d0[0], d0[1]);
        if (d1) w.points = rubber({ orig: clone(w.points), a0: false, a1: true }, d1[0], d1[1]);
      }
      w.points = simplify(w.points);
    }
    for (const [id, [dx, dy]] of deltas) {
      const e = byId(id);
      if (!e) continue;
      if ('x' in e) { e.x += dx; e.y += dy; }
      if (e.points) e.points = e.points.map(([x, y]) => [x + dx, y + dy]);
    }
  });
}

const alignable = () => selected().filter((e) => e.type !== 'wire' && e.type !== 'arrow' && !e.locked);

export function align(mode) {
  const items = alignable();
  if (items.length < 2) { toast('Select two or more parts, texts or boxes to align'); return; }
  const g = D().page.grid || 5, bb = new Map(items.map((e) => [e.id, bboxOf(e, false)]));
  const all = [...bb.values()];
  const minx = Math.min(...all.map((b) => b[0])), maxx = Math.max(...all.map((b) => b[2]));
  const miny = Math.min(...all.map((b) => b[1])), maxy = Math.max(...all.map((b) => b[3]));
  const deltas = new Map();
  for (const [id, b] of bb) {
    const dx = { left: minx - b[0], right: maxx - b[2], center: (minx + maxx) / 2 - (b[0] + b[2]) / 2 }[mode] ?? 0;
    const dy = { top: miny - b[1], bottom: maxy - b[3], middle: (miny + maxy) / 2 - (b[1] + b[3]) / 2 }[mode] ?? 0;
    if (dx || dy) deltas.set(id, [snapTo(dx, g), snapTo(dy, g)]);
  }
  moveEach(deltas);
}

export function distribute(axis) {
  const items = alignable();
  if (items.length < 3) { toast('Select three or more parts, texts or boxes to distribute'); return; }
  const g = D().page.grid || 5, i0 = axis === 'h' ? 0 : 1;
  const c = (e) => { const b = bboxOf(e, false); return (b[i0] + b[i0 + 2]) / 2; };
  const sorted = [...items].sort((a, b) => c(a) - c(b));
  const first = c(sorted[0]), step = (c(sorted.at(-1)) - first) / (sorted.length - 1);
  const deltas = new Map();
  sorted.forEach((e, i) => {
    const d = snapTo(first + step * i - c(e), g);
    if (d) deltas.set(e.id, axis === 'h' ? [d, 0] : [0, d]);
  });
  moveEach(deltas);
}
