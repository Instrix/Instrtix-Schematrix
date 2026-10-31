import { svgInner, widthChars } from './markup.js';

// Placement maths: the JS twin of schematrix/geometry.py and render.py (keep the two in step).

export const LINE_H = 14;
export const FONT_SIZES = { lbl: 12, ref: 12, val: 11.5, valsm: 10.5, node: 12, net: 11, pin: 13, termlbl: 12.5,
  accl: 12, grplbl: 10, note: 12, title: 15 };
const CTR = { pin: 4, net: 4, lbl: 4 };       // whole pixels, as the original figures centred them

export function xf(px, py, rot = 0, mirror = false) {
  if (mirror) px = -px;
  const r = ((rot % 360) + 360) % 360;
  if (r === 90) return [-py, px];
  if (r === 180) return [-px, -py];
  if (r === 270) return [py, -px];
  return [px, py];
}

export const r2 = (v) => Math.round(v * 100) / 100;

export function place(c, px, py) {
  const [dx, dy] = xf(px, py, c.rot || 0, !!c.mirror);
  return [r2(c.x + dx), r2(c.y + dy)];
}

export function textAnchor(a, rot, mirror) {
  if (a === 'middle') return a;
  const [dx] = xf(1, 0, rot, mirror);
  if (dx < 0) return a === 'start' ? 'end' : 'start';
  return a;
}

export const ctrOffset = (cls) => CTR[cls] ?? Math.round((FONT_SIZES[cls] ?? 12) * 0.35 * 100) / 100;

export function textWidth(s, cls = 'lbl') {
  const fs = FONT_SIZES[cls] ?? 12;
  return widthChars(s) * fs * (cls === 'note' || cls === 'title' ? 0.55 : 0.6);
}

export function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

export function num(v) {
  const r = Math.round(Number(v) * 100) / 100;
  return String(r);
}

export function styleCls(base, style) {
  const toks = base.split(/\s+/).filter(Boolean);
  const st = (style || '').split(/\s+/).filter(Boolean);
  if (!st.length) return base;
  if (toks.includes('w')) { for (const s of st) if (!toks.includes(s)) toks.push(s); }
  else if (['amp', 'arrow', 'dot'].includes(toks[0]) && st.includes('acc')) toks.push('acc');
  return toks.join(' ');
}

// ---------------------------------------------------------------- label block
export function labelLines(c, sym, g) {
  const props = { ...defaults(sym), ...(c.props || {}) };
  const acc = (c.style || '').split(/\s+/).includes('acc');
  const out = [];
  for (const [key, cls] of g.lines) {
    const s = String(props[key] ?? '');
    if (s) out.push([s, acc && cls === 'ref' ? 'accl' : cls, key]);
  }
  for (const f of c.fields || []) if (f.show && String(f.value ?? '')) out.push([String(f.value), 'valsm', 'f:' + f.name]);
  return out;
}

export function defaults(sym) {
  const d = {};
  for (const [k, p] of Object.entries(sym?.props || {})) d[k] = p.default;
  return d;
}

export function labelBlock(c, sym, g) {
  if (c.hide_labels || !g) return [];
  const lines = labelLines(c, sym, g);
  if (!lines.length) return [];
  const lb = g.label;
  let [px, py] = place(c, lb.x, lb.y);
  const [nx, ny] = xf(lb.nx, lb.ny, c.rot || 0, !!c.mirror);
  if (c.label_offset) { px += c.label_offset[0]; py += c.label_offset[1]; }
  const k = lines.length, res = [];
  if (Math.abs(nx) > 0.5) {
    const a = nx > 0 ? 'start' : 'end';
    lines.forEach(([s, cl, kk], i) => res.push([px, py - (k - 1) * LINE_H / 2 + 4 + i * LINE_H, s, cl, a, kk]));
  } else if (ny < 0) {
    lines.forEach(([s, cl, kk], i) => res.push([px, py - (k - 1 - i) * LINE_H, s, cl, 'middle', kk]));
  } else {
    lines.forEach(([s, cl, kk], i) => res.push([px, py + 10 + i * LINE_H, s, cl, 'middle', kk]));
  }
  return res.map(([x, y, s, cl, a, kk]) => [r2(x), r2(y), s, cl, a, kk]);
}

// ---------------------------------------------------------------- svg markup
export function primSvg(p, c, style) {
  const rot = c ? c.rot || 0 : 0, mir = c ? !!c.mirror : false;
  const P = c ? (x, y) => place(c, x, y) : (x, y) => [x, y];
  const cl = styleCls(p.c, style);
  switch (p.k) {
    case 'pl': case 'pg': {
      const pts = p.pts.map(([x, y]) => P(x, y).map(num).join(',')).join(' ');
      return `<${p.k === 'pl' ? 'polyline' : 'polygon'} class="${cl}" points="${pts}"/>`;
    }
    case 'ci': { const [x, y] = P(p.x, p.y); return `<circle class="${cl}" cx="${num(x)}" cy="${num(y)}" r="${num(p.r)}"/>`; }
    case 'rc': {
      const [ax, ay] = P(p.x, p.y), [bx, by] = P(p.x + p.w, p.y + p.h);
      return `<rect class="${cl}" x="${num(Math.min(ax, bx))}" y="${num(Math.min(ay, by))}" width="${num(Math.abs(bx - ax))}" height="${num(Math.abs(by - ay))}" rx="${num(p.rx || 0)}"/>`;
    }
    case 'tx': {
      let [x, y] = P(p.x, p.y);
      const z = p.z || 1;
      if (p.ctr) y += ctrOffset(p.c) * z;
      const fs = z !== 1 ? ` style="font-size:${num((FONT_SIZES[p.c] || 12) * z)}px"` : '';
      return `<text class="${p.c}" x="${num(x)}" y="${num(y)}" text-anchor="${textAnchor(p.a || 'middle', rot, mir)}"${fs}>${svgInner(p.s, (FONT_SIZES[p.c] || 12) * z, esc)}</text>`;
    }
  }
  return '';
}

export const textSvg = (x, y, s, cls = 'lbl', a = 'middle') =>
  `<text class="${cls}" x="${num(x)}" y="${num(y)}" text-anchor="${a}">${svgInner(s, FONT_SIZES[cls] ?? 12, esc)}</text>`;

// direction marks on a wire: [distance along it to the head's base, length, half-width]; negative length points back
export function wireMarks(e) {
  const P = e.points || [], cls = (e.style || '').split(/\s+/).includes('acc') ? 'accf' : 'arrow';
  let out = '';
  for (const m of e.marks || []) {
    let [rem, L, W] = m.map(Number);
    for (let i = 0; i < P.length - 1; i++) {
      const a = P[i], b = P[i + 1], n = Math.hypot(b[0] - a[0], b[1] - a[1]);
      if (rem <= n || i === P.length - 2) {
        const u = [(b[0] - a[0]) / (n || 1), (b[1] - a[1]) / (n || 1)], base = [a[0] + u[0] * rem, a[1] + u[1] * rem];
        out += arrowHead(base, [base[0] + u[0] * L, base[1] + u[1] * L], cls, Math.abs(L), W);
        break;
      }
      rem -= n;
    }
  }
  return out;
}

export function arrowHead(a, b, cls = 'arrow', L = 9, W = 4) {
  const dx = b[0] - a[0], dy = b[1] - a[1], n = Math.hypot(dx, dy) || 1, ux = dx / n, uy = dy / n;
  const bx = b[0] - ux * L, by = b[1] - uy * L;
  const pts = [[b[0], b[1]], [bx - uy * W, by + ux * W], [bx + uy * W, by - ux * W]];
  return `<polygon class="${cls}" points="${pts.map((p) => p.map(num).join(',')).join(' ')}"/>`;
}

const ptsAttr = (P) => P.map((p) => p.map(num).join(',')).join(' ');

export function elementSvg(e, cat, geoOf, hop) {
  switch (e.type) {
    case 'comp': {
      const g = geoOf(e);
      if (!g) return `<circle class="dot" cx="${e.x}" cy="${e.y}" r="2"/>`;
      let s = g.prims.map((p) => primSvg(p, e, e.style || '')).join('');
      s += labelBlock(e, cat[e.sym], g).map(([x, y, t, c, a, k]) => `<g data-label="${k}">${textSvg(x, y, t, c, a)}</g>`).join('');
      return s;
    }
    case 'wire':
      if ((e.points || []).length < 2) return '';
      if (hop) return `<path class="${styleCls('w wire', e.style)}" d="${wirePath(e.points, hop)}"/>` + wireMarks(e);
      return `<polyline class="${styleCls('w wire', e.style)}" points="${ptsAttr(e.points)}"/>` + wireMarks(e);
    case 'arrow': {
      const P = e.points || [];
      if (P.length < 2) return '';
      const st = e.style || '', a = P[P.length - 2], b = P[P.length - 1];
      const [L, W] = (e.head || [9, 4]).map(Number), cut = L * 2 / 3;   // the line stops inside the head
      const n = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
      const tip = [b[0] - (b[0] - a[0]) / n * cut, b[1] - (b[1] - a[1]) / n * cut];
      return `<polyline class="${styleCls('w', st)}" points="${ptsAttr([...P.slice(0, -1), tip])}"/>` +
        arrowHead(a, b, st.split(/\s+/).includes('acc') ? 'accf' : 'arrow', L, W);
    }
    case 'text': {
      const cls = e.cls || 'lbl', lh = cls === 'note' || cls === 'title' ? 16 : 14;
      return String(e.text ?? '').split('\n').map((l, i) => (l === '' ? '' : textSvg(e.x, e.y + lh * i, l, cls, e.anchor || 'start'))).join('');
    }
    case 'rect': {
      let s = `<rect class="${e.cls || 'grp'}" x="${num(e.x)}" y="${num(e.y)}" width="${num(e.w)}" height="${num(e.h)}" rx="${num(e.rx ?? 4)}"${e.css ? ` style="${esc(e.css)}"` : ''}/>`;
      if (e.label) s += textSvg(e.x + 4, e.y + 12, e.label, e.label_cls || 'grplbl', 'start');
      return s;
    }
    case 'raw': {
      const x = e.x || 0, y = e.y || 0;
      return x || y ? `<g transform="translate(${num(x)} ${num(y)})">${e.svg || ''}</g>` : e.svg || '';
    }
  }
  return '';
}

// ---------------------------------------------------------------- connectivity
export const key = (p) => `${Math.round(p[0] * 2) / 2},${Math.round(p[1] * 2) / 2}`;

export function onSegment(p, a, b, eps = 0.6) {
  const [x, y] = p, [x1, y1] = a, [x2, y2] = b;
  if (key(p) === key(a) || key(p) === key(b)) return false;
  if (Math.min(x1, x2) - eps > x || x > Math.max(x1, x2) + eps || Math.min(y1, y2) - eps > y || y > Math.max(y1, y2) + eps) return false;
  const cross = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1);
  const L = Math.hypot(x2 - x1, y2 - y1) || 1;
  return Math.abs(cross) / L < eps;
}

export function compPins(c, g) {
  if (!g) return {};
  const o = {};
  for (const [k, [x, y]] of Object.entries(g.pins)) o[k] = place(c, x, y);
  return o;
}

export function connectionPoints(doc, geoOf) {
  const wires = doc.elements.filter((e) => e.type === 'wire' && (e.points || []).length >= 2);
  const pts = [];
  for (const e of doc.elements) {
    if (e.type === 'comp' && e.sym !== 'dot' && e.sym !== 'busentry') {
      for (const [n, p] of Object.entries(compPins(e, geoOf(e)))) pts.push([p, 'pin', e.id, n]);
    }
  }
  for (const w of wires) {
    const P = w.points;
    P.forEach((p, i) => pts.push([p, i === 0 || i === P.length - 1 ? 'end' : 'mid', w.id, i]));
  }
  return { wires, pts };
}

export function junctions(doc, geoOf) {
  const { wires, pts: all } = connectionPoints(doc, geoOf);
  const labels = new Set(doc.elements.filter((e) => e.type === 'comp' && e.sym === 'flag').map((e) => e.id));
  const pts = all.filter(([, kind, id]) => !(kind === 'pin' && labels.has(id)));      // net labels make no dots
  const deg = new Map(), where = new Map();
  for (const [p, kind] of pts) {
    const k = key(p);
    where.set(k, p);
    deg.set(k, (deg.get(k) || 0) + (kind === 'mid' ? 2 : 1));
  }
  for (const [k, p] of where) {
    for (const w of wires) {
      const P = w.points;
      for (let i = 0; i + 1 < P.length; i++) if (onSegment(p, P[i], P[i + 1])) deg.set(k, deg.get(k) + 2);
    }
  }
  return [...deg].filter(([, d]) => d >= 3).map(([k]) => where.get(k));
}

export const HOP_R = 4;

// wire id -> {segment index: [crossing points]} where a horizontal wire jumps over a vertical one
export function hops(doc, geoOf, r = HOP_R) {
  const { wires, pts } = connectionPoints(doc, geoOf);
  const conn = new Set(pts.map(([p]) => key(p)));
  const H = [], V = [];
  for (const w of wires) {
    const P = w.points;
    for (let i = 0; i + 1 < P.length; i++) {
      const [a, b] = [P[i], P[i + 1]];
      if (a[1] === b[1] && a[0] !== b[0]) H.push([w.id, i, a, b]);
      else if (a[0] === b[0] && a[1] !== b[1]) V.push([a, b]);
    }
  }
  const out = {};
  for (const [wid, i, a, b] of H) {
    const x0 = Math.min(a[0], b[0]), x1 = Math.max(a[0], b[0]), y = a[1];
    for (const [c, d] of V) {
      const x = c[0], y0 = Math.min(c[1], d[1]), y1 = Math.max(c[1], d[1]);
      if (x0 + r <= x && x <= x1 - r && y0 < y && y < y1 && !conn.has(key([x, y]))) ((out[wid] ??= {})[i] ??= []).push([x, y]);
    }
  }
  return out;
}

// SVG path data for a wire, with a semicircle (bulging up) at each hop on its horizontal segments
export function wirePath(P, hop, r = HOP_R) {
  const d = [`M${num(P[0][0])} ${num(P[0][1])}`];
  for (let i = 0; i + 1 < P.length; i++) {
    const [a, b] = [P[i], P[i + 1]], s = b[0] > a[0] ? 1 : -1;
    for (const [x, y] of [...(hop?.[i] || [])].sort((p, q) => (p[0] - q[0]) * s)) {
      d.push(`L${num(x - s * r)} ${num(y)}A${num(r)} ${num(r)} 0 0 ${s > 0 ? 1 : 0} ${num(x + s * r)} ${num(y)}`);
    }
    d.push(`L${num(b[0])} ${num(b[1])}`);
  }
  return d.join('');
}

// ---------------------------------------------------------------- bounding boxes
export function compBBox(c, sym, g) {
  if (!g) return [c.x - 5, c.y - 5, c.x + 5, c.y + 5];
  const [x0, y0, x1, y1] = g.bbox;
  const a = place(c, x0, y0), b = place(c, x1, y1);
  return [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[0], b[0]), Math.max(a[1], b[1])];
}

export function labelBBox(c, sym, g) {
  const L = labelBlock(c, sym, g);
  if (!L.length) return null;
  const xs = [], ys = [];
  for (const [x, y, s, cl, a] of L) {
    const w = textWidth(s, cl), lx = x - (a === 'middle' ? w / 2 : a === 'end' ? w : 0);
    xs.push(lx, lx + w); ys.push(y - 11, y + 3);
  }
  return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
}

export function elementBBox(e, cat, geoOf, withLabels = true) {
  switch (e.type) {
    case 'comp': {
      const g = geoOf(e), b = compBBox(e, cat[e.sym], g);
      if (!withLabels) return b;
      const lb = labelBBox(e, cat[e.sym], g);
      return lb ? [Math.min(b[0], lb[0]), Math.min(b[1], lb[1]), Math.max(b[2], lb[2]), Math.max(b[3], lb[3])] : b;
    }
    case 'wire': case 'arrow': {
      const xs = e.points.map((p) => p[0]), ys = e.points.map((p) => p[1]);
      return xs.length ? [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)] : null;
    }
    case 'rect': return [e.x, e.y, e.x + e.w, e.y + e.h];
    case 'text': {
      const lines = String(e.text ?? '').split('\n'), cls = e.cls || 'lbl';
      const w = Math.max(...lines.map((l) => textWidth(l, cls))), a = e.anchor || 'start';
      const x0 = e.x - (a === 'middle' ? w / 2 : a === 'end' ? w : 0);
      return [x0, e.y - 12, x0 + w, e.y + 4 + 16 * (lines.length - 1)];
    }
    case 'raw': return e.bbox ? [e.bbox[0] + (e.x || 0), e.bbox[1] + (e.y || 0), e.bbox[2] + (e.x || 0), e.bbox[3] + (e.y || 0)] : null;
  }
  return null;
}
