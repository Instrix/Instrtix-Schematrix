// Canvas tools: placing, wire drawing, moving, KiCad-style wire dragging, pointer input, net labels and inline text editing.
import * as G from './geom.js';
import { closeMenus } from './commands.js';
import { renderInspector, seg } from './inspector.js';
import { buildPalette } from './palette.js';
import { byId, changed, D, edit, geoOf, nextId, nextRef, pinsOf, pushUndo, S, selected, snapshot, T } from './state.js';
import { ask, contextMenu } from './ui.js';
import { $, $$, clone, snapTo, svg } from './util.js';
import { applyView, bboxOf, overlaySoon, renderSoon, fit, render, renderOverlay, renderStatus, toScreen, toWorld, zoomAt } from './view.js';

// ---------------------------------------------------------------- tools
export function setTool(t) {
  if (S.draft) finishDraft();
  S.tool = t; S.placing = t === 'place' ? S.placing : null; S.ghost = null;
  svg.className.baseVal = 'tool-' + t;
  $$('#tools button').forEach((b) => b.classList.toggle('on', b.dataset.tool === t));
  $$('.sym').forEach((b) => b.classList.remove('on'));
  renderOverlay(); renderStatus();
}
export function startPlacing(sym, props = {}) {
  setTool('place');
  S.placing = { sym, props, rot: 0, mirror: false };
  buildPalette($('#symsearch').value);
  updateGhost(S.mouse);
  svg.focus();
}
export function updateGhost(w) {
  if (!S.placing) return;
  const g = D().page.grid || 5;
  const { sym, props, rot, mirror } = S.placing;
  S.ghost = { id: 'ghost', type: 'comp', sym, x: snapTo(w[0], g), y: snapTo(w[1], g), rot, mirror, props: { ...props }, style: S.style === 'bus' ? '' : S.style };
  overlaySoon();
}
export function placeAt(w) {
  const { sym, props, rot, mirror } = S.placing, c = S.cat[sym], g = D().page.grid || 5;
  edit((d) => {
    const el = { id: nextId(d), type: 'comp', sym, x: snapTo(w[0], g), y: snapTo(w[1], g), rot, mirror, props: { ...props }, style: S.style === 'bus' ? '' : S.style };
    if (c.props.ref && !props.ref) el.props.ref = nextRef(c.prefix, d);
    d.elements.push(el);
    T().sel = new Set([el.id]);
  });
}

const isBus = (e) => (e.style || '').split(/\s+/).includes('bus');
// snapping for wire ends: pins and wire vertices first, then wire segments, then the grid; bus pins and bus wires
// report bus: true so a wire drawn from or onto them becomes a bus
export function snapPoint(w, excludeWire) {
  const k = T().view.k, R = 9 / k, g = D().page.grid || 5;
  let best = null, bd = R;
  for (const e of D().elements) {
    if (e.type === 'comp') {
      const buses = geoOf(e)?.buses || {};
      for (const [n, p] of Object.entries(pinsOf(e))) { const dd = Math.hypot(p[0] - w[0], p[1] - w[1]); if (dd < bd) { bd = dd; best = [p, 'pin', n in buses]; } }
    }
    if (e.type === 'wire' && e.id !== excludeWire) for (const p of e.points) { const dd = Math.hypot(p[0] - w[0], p[1] - w[1]); if (dd < bd) { bd = dd; best = [p, 'wire', isBus(e)]; } }
  }
  if (best) return { p: [...best[0]], kind: best[1], bus: best[2] };
  for (const e of D().elements) {
    if (e.type !== 'wire' || e.id === excludeWire) continue;
    for (let i = 0; i + 1 < e.points.length; i++) {
      const [a, b] = [e.points[i], e.points[i + 1]];
      if (a[1] === b[1] && Math.abs(w[1] - a[1]) < 6 / k && w[0] > Math.min(a[0], b[0]) && w[0] < Math.max(a[0], b[0])) return { p: [snapTo(w[0], g), a[1]], kind: 'seg', bus: isBus(e) };
      if (a[0] === b[0] && Math.abs(w[0] - a[0]) < 6 / k && w[1] > Math.min(a[1], b[1]) && w[1] < Math.max(a[1], b[1])) return { p: [a[0], snapTo(w[1], g)], kind: 'seg', bus: isBus(e) };
    }
  }
  return { p: [snapTo(w[0], g), snapTo(w[1], g)], kind: 'grid' };
}
export function elbow(a, c, prevDir) {
  if (a[0] === c[0] || a[1] === c[1]) return [];
  let mode = S.wireMode;
  if (mode === 'auto') mode = prevDir === 'h' ? 'vh' : prevDir === 'v' ? 'hv' : Math.abs(c[0] - a[0]) >= Math.abs(c[1] - a[1]) ? 'hv' : 'vh';
  return mode === 'hv' ? [[c[0], a[1]]] : [[a[0], c[1]]];
}
export function draftPath() {
  const dr = S.draft, pts = dr.pts, a = pts[pts.length - 1];
  if (dr.kind === 'arrow') return [...pts, dr.cur];
  let prevDir = null;
  if (pts.length >= 2) { const p = pts[pts.length - 2]; prevDir = p[1] === a[1] ? 'h' : p[0] === a[0] ? 'v' : null; }
  return [...pts, ...elbow(a, dr.cur, prevDir), dr.cur];
}
export function simplify(P) {
  const out = [];
  for (const p of P) { if (!out.length || G.key(out[out.length - 1]) !== G.key(p)) out.push([p[0], p[1]]); }
  for (let i = out.length - 2; i >= 1; i--) {
    const [a, b, c] = [out[i - 1], out[i], out[i + 1]];
    if ((a[0] === b[0] && b[0] === c[0]) || (a[1] === b[1] && b[1] === c[1])) out.splice(i, 1);
  }
  return out;
}
export function draftClick(w, ev) {
  const sn = S.draft?.kind === 'arrow' || S.tool === 'arrow' ? { p: [snapTo(w[0], D().page.grid || 5), snapTo(w[1], D().page.grid || 5)], kind: 'grid' } : snapPoint(w);
  if (!S.draft) { S.draft = { kind: S.tool, pts: [sn.p], cur: sn.p, snapKind: sn.kind, bus: !!sn.bus }; renderOverlay(); renderStatus(); return; }
  const dr = S.draft;
  dr.cur = sn.p;
  if (sn.bus && dr.pts.length === 1 && !dr.bus) dr.bus = sn.kind === 'pin';     // started on a plain point, ends on a bus pin
  const path = draftPath();
  const last = dr.pts[dr.pts.length - 1];
  if (G.key(last) === G.key(sn.p) && dr.pts.length >= 2) { finishDraft(); return; }
  dr.pts = path;
  if (dr.kind === 'wire' && sn.kind !== 'grid' && dr.pts.length >= 2) finishDraft();
  else renderOverlay();
}
export function finishDraft() {
  const dr = S.draft;
  S.draft = null;
  if (!dr) return;
  const P = dr.kind === 'arrow' ? dr.pts : simplify(dr.pts);
  if (P.length >= 2) {
    edit((d) => {
      const el = { id: nextId(d), type: dr.kind, points: P, style: dr.kind === 'arrow' ? S.style || 'acc' : dr.bus ? 'bus' : S.style };
      d.elements.push(el);
    });
  } else render();
  renderStatus();
}

// ---------------------------------------------------------------- moving with rubber-banding
export function startMove(w) {
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
  // T junctions: other wires whose end sits on the middle of a wire that is about to stretch ride along with it
  const hosts = new Set(attached.map((a) => a.id)), tees = [];
  for (const e of D().elements) {
    if (e.type !== 'wire' || ids.has(e.id) || hosts.has(e.id) || e.points.length < 2) continue;
    const n = e.points.length;
    for (const host of attached) {
      const on = (p) => host.orig.some((q, i) => i + 1 < host.orig.length && G.onSegment(p, q, host.orig[i + 1]));
      const t0 = on(e.points[0]), t1 = on(e.points[n - 1]);
      if (t0 || t1) { tees.push({ id: e.id, orig: clone(e.points), a0: t0, a1: t1, host: host.id }); break; }
    }
  }
  S.drag = { kind: 'move', start: w, orig, attached, tees, snap: snapshot(), moved: false };
}
export function applyMove(dx, dy) {
  const dr = S.drag;
  for (const [id, o] of dr.orig) {
    const e = byId(id);
    if (!e) continue;
    if ('x' in o) { e.x = o.x + dx; e.y = o.y + dy; }
    if (o.points) e.points = o.points.map(([x, y]) => [x + dx, y + dy]);
  }
  for (const a of dr.attached) { const e = byId(a.id); if (e) e.points = rubber(a, dx, dy); }
  for (const t of dr.tees || []) {                       // re-seat each T end on the host's new path
    const e = byId(t.id), host = byId(t.host);
    if (!e || !host) continue;
    const end = t.a0 ? t.orig[0] : t.orig[t.orig.length - 1];
    let best = end, bd = Infinity;
    for (let i = 0; i + 1 < host.points.length; i++) {
      const [a, b] = [host.points[i], host.points[i + 1]];
      const q = a[1] === b[1] ? [Math.min(Math.max(end[0], Math.min(a[0], b[0])), Math.max(a[0], b[0])), a[1]]
        : [a[0], Math.min(Math.max(end[1], Math.min(a[1], b[1])), Math.max(a[1], b[1]))];
      const d = Math.hypot(q[0] - end[0], q[1] - end[1]);
      if (d < bd) { bd = d; best = q; }
    }
    e.points = rubber({ orig: t.orig, a0: t.a0, a1: !t.a0 && t.a1 }, best[0] - end[0], best[1] - end[1]);
  }
}
// a wire with one or both ends on something moving by (dx, dy): drag those ends and keep the wire orthogonal
export function rubber(a, dx, dy) {
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
export function connectedAt(p, wid) {
  const k = G.key(p);
  for (const e of D().elements) {
    if (e.type === 'comp' && (e.sym === 'dot' ? G.key([e.x, e.y]) === k : Object.values(pinsOf(e)).some((q) => G.key(q) === k))) return true;
    if (e.type !== 'wire' || e.id === wid) continue;
    if (e.points.some((q) => G.key(q) === k)) return true;
    for (let i = 0; i + 1 < e.points.length; i++) if (G.onSegment(p, e.points[i], e.points[i + 1])) return true;
  }
  return false;
}
export function segDist(p, a, b) {
  const [vx, vy] = [b[0] - a[0], b[1] - a[1]], L = vx * vx + vy * vy;
  const t = L ? Math.max(0, Math.min(1, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / L)) : 0;
  return Math.hypot(p[0] - a[0] - t * vx, p[1] - a[1] - t * vy);
}
export function startWireDrag(e, w, end) {
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
export function applyWireDrag(w) {
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
export function endDrag() {
  const dr = S.drag;
  S.drag = null;
  if (!dr) return;
  if (['move', 'vertex', 'label', 'resize', 'wend', 'wseg'].includes(dr.kind)) {
    for (const a of [...(dr.attached || []), ...(dr.tees || [])]) { const e = byId(a.id); if (e) e.points = simplify(e.points); }
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
      if (e.locked) continue;
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
  if (ev.button === 2) {                  // right button: drag pans; a click without movement opens the menu on release
    S.drag = { kind: 'pan', sx: ev.clientX, sy: ev.clientY, vx: T().view.x, vy: T().view.y, right: true, moved: false,
      target: ev.target.closest('#content [data-id]')?.dataset.id };
    svg.setPointerCapture(ev.pointerId); ev.preventDefault(); return;
  }
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
  if (dr?.kind === 'pan' && dr.right && !dr.moved) {
    if (Math.hypot(ev.clientX - dr.sx, ev.clientY - dr.sy) < 4) return;
    dr.moved = true; svg.classList.add('panning');
  }
  if (dr?.kind === 'pan') { T().fitPending = false; T().view.x = dr.vx + ev.clientX - dr.sx; T().view.y = dr.vy + ev.clientY - dr.sy; applyView(); return; }
  if (S.placing) { updateGhost(w); return; }
  if (S.draft) {
    const sn = S.draft.kind === 'arrow' ? { p: [snapTo(w[0], g), snapTo(w[1], g)], kind: 'grid' } : snapPoint(w);
    S.draft.cur = sn.p; S.draft.snapKind = sn.kind; overlaySoon(); return;
  }
  if (!dr && (S.tool === 'wire' || S.tool === 'flag' || S.tool === 'arrow')) {
    const sn = S.tool === 'arrow' ? { p: [snapTo(w[0], g), snapTo(w[1], g)], kind: 'grid' } : snapPoint(w);
    S.hover = sn.p; S.hoverKind = sn.kind; overlaySoon(); return;
  }
  if (!dr) return;
  if (dr.kind === 'move') {
    const dx = snapTo(w[0] - dr.start[0], g), dy = snapTo(w[1] - dr.start[1], g);
    if (dx !== dr.dx || dy !== dr.dy) { dr.dx = dx; dr.dy = dy; applyMove(dx, dy); renderSoon(); }
  } else if (dr.kind === 'wend' || dr.kind === 'wseg') {
    applyWireDrag(w); renderSoon();
  } else if (dr.kind === 'vertex') {
    const e = byId(dr.id), sn = e.type === 'wire' ? snapPoint(w, e.id) : { p: [snapTo(w[0], g), snapTo(w[1], g)] };
    e.points[dr.idx] = sn.p; renderSoon();
  } else if (dr.kind === 'label') {
    const e = byId(dr.id);
    e.label_offset = [dr.orig[0] + Math.round(w[0] - dr.start[0]), dr.orig[1] + Math.round(w[1] - dr.start[1])]; renderSoon();
  } else if (dr.kind === 'resize') {
    const e = byId(dr.id);
    e.w = Math.max(10, snapTo(w[0], g) - e.x); e.h = Math.max(10, snapTo(w[1], g) - e.y); renderSoon();
  } else if (dr.kind === 'marquee') { dr.cur = w; overlaySoon(); } else if (dr.kind === 'rect') { dr.cur = [snapTo(w[0], g), snapTo(w[1], g)]; overlaySoon(); }
});

svg.addEventListener('pointerup', (ev) => {
  if (S.drag?.kind === 'pan') {
    const dr = S.drag;
    S.drag = null; svg.classList.remove('panning');
    if (dr.right && !dr.moved) { if (S.draft) finishDraft(); else showContextMenu(ev.clientX, ev.clientY, dr.target); }
    return;
  }
  endDrag();
});
svg.addEventListener('contextmenu', (ev) => ev.preventDefault());
function showContextMenu(x, y, id) {
  if (S.tool !== 'select') return;
  const t = T();
  if (id && !t.sel.has(id)) { t.sel = new Set([id]); render(); renderInspector(); }
  const many = t.sel.size > 1 ? [['Align left', 'align-left'], ['Align centres', 'align-center'], ['Align top', 'align-top'],
    ['Align middles', 'align-middle'], ['Distribute horizontally', 'distribute-h'], ['Distribute vertically', 'distribute-v'], null] : [];
  const items = t.sel.size ? [...many,
    ['Bring to front', 'front', 'Ctrl ]'], ['Bring forward', 'forward', 'PgUp'], ['Send backward', 'backward', 'PgDn'],
    ['Send to back', 'back', 'Ctrl ['], null,
    ['Rotate', 'rotate', 'R'], ['Mirror', 'mirror', 'M'], ['Toggle accent', 'accent', 'E'], null,
    ['Cut', 'cut', 'Ctrl X'], ['Copy', 'copy', 'Ctrl C'], ['Duplicate', 'duplicate', 'Ctrl D'], null,
    ...(selected().some((e) => e.type === 'wire') ? [['Auto-route wire', 'autoroute', ''], null] : []),
    ['Copy as image', 'copy-image', 'Ctrl Shift C'], ['Export selection…', 'export-selection', ''], ['Delete', 'delete', 'Del'],
  ] : [['Paste', 'paste', 'Ctrl V'], ['Select all', 'selectall', 'Ctrl A'], null, ['Fit to page', 'fit', 'F'],
    ['Copy as image', 'copy-image', 'Ctrl Shift C'], ['Export…', 'export', 'Ctrl E']];
  contextMenu(x, y, items);
}
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
export async function placeFlag(w) {
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
export function inlineEdit(e, key) {
  const ta = $('#inlineedit');
  let value, anchor, cls;
  if (e.type === 'text') { value = e.text; anchor = [e.x, e.y]; cls = e.cls; } else if (e.type === 'rect') { value = e.label || ''; anchor = [e.x + 4, e.y + 12]; } else {
    const c = S.cat[e.sym];
    value = key.startsWith('f:') ? String(e.fields?.find((f) => 'f:' + f.name === key)?.value ?? '')
      : String(e.props?.[key] ?? c?.props[key]?.default ?? '');
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
      else if (key.startsWith('f:')) { const f = e.fields?.find((x) => 'f:' + x.name === key); if (f) f.value = ta.value; }
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
