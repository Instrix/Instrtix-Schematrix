"""Placement maths shared by the renderer and the netlister (the web editor has a line-for-line JS twin in
web/js/geom.js: keep the two in step)."""
from __future__ import annotations

from . import symbols as SYM

LINE_H = 14


def xf(px, py, rot=0, mirror=False):
    """local -> placed offset: mirror local x, then rotate clockwise by rot (multiple of 90)"""
    if mirror:
        px = -px
    r = int(rot) % 360
    if r == 90:
        return -py, px
    if r == 180:
        return -px, -py
    if r == 270:
        return py, -px
    return px, py


def place(comp, px, py):
    dx, dy = xf(px, py, comp.get('rot', 0), comp.get('mirror', False))
    return round(comp['x'] + dx, 2), round(comp['y'] + dy, 2)


def text_anchor(a, rot, mirror):
    """an upright text keeps reading left to right: flip start/end when local +x ends up pointing left"""
    if a == 'middle':
        return a
    dx, _ = xf(1, 0, rot, mirror)
    if dx < 0:
        return 'end' if a == 'start' else 'start'
    return a


CTR = {'pin': 4, 'net': 4}


def ctr_offset(cls):
    """baseline shift that puts a text's visual centre on its anchor point"""
    return CTR.get(cls, round(SYM.FONT_SIZES.get(cls, 12) * 0.35, 2))


_geo_cache: dict = {}


def geometry(comp):
    sym = SYM.get(comp['sym'])
    props = comp.get('props', {})
    key = (comp['sym'], tuple((k, str(props.get(k))) for k in sym.geom_keys()))
    g = _geo_cache.get(key)
    if g is None:
        g = sym.geometry({k: props[k] for k in sym.geom_keys() if k in props})
        if len(_geo_cache) > 4096:
            _geo_cache.clear()
        _geo_cache[key] = g
    return g


def pins(comp):
    """{pin name: (x, y)} in sheet coordinates"""
    return {k: place(comp, *v) for k, v in geometry(comp)['pins'].items()}


def label_lines(comp, sym=None, g=None):
    sym = sym or SYM.get(comp['sym'])
    g = g or geometry(comp)
    props = {**sym.defaults(), **comp.get('props', {})}
    acc = 'acc' in (comp.get('style') or '')
    out = []
    for key, cls in g['lines']:
        s = str(props.get(key, '') or '')
        if s:
            out.append((s, 'accl' if acc and cls == 'ref' else cls))
    for f in comp.get('fields') or []:          # user fields marked 'show' print their value under the rest
        if f.get('show') and str(f.get('value', '')):
            out.append((str(f['value']), 'valsm'))
    return out


def label_block(comp):
    """[(x, y, text, cls, anchor)] for the component's label block, honouring a dragged label_offset"""
    if comp.get('hide_labels'):
        return []
    g = geometry(comp)
    lines = label_lines(comp, g=g)
    if not lines:
        return []
    lb = g['label']
    rot, mir = comp.get('rot', 0), comp.get('mirror', False)
    px, py = place(comp, lb['x'], lb['y'])
    nx, ny = xf(lb['nx'], lb['ny'], rot, mir)
    off = comp.get('label_offset')
    if off:
        px += off[0]; py += off[1]
    k = len(lines)
    res = []
    if abs(nx) > 0.5:
        a = 'start' if nx > 0 else 'end'
        for i, (s, c) in enumerate(lines):
            res.append((px, py - (k - 1) * LINE_H / 2 + 4 + i * LINE_H, s, c, a))
    elif ny < 0:
        for i, (s, c) in enumerate(lines):
            res.append((px, py - (k - 1 - i) * LINE_H, s, c, 'middle'))
    else:
        for i, (s, c) in enumerate(lines):
            res.append((px, py + 10 + i * LINE_H, s, c, 'middle'))
    return [(round(x, 2), round(y, 2), s, c, a) for x, y, s, c, a in res]


def _key(p):
    return (round(p[0] * 2) / 2, round(p[1] * 2) / 2)


def on_segment(p, a, b, eps=0.6):
    """p strictly inside segment a-b (not at its ends)"""
    (x, y), (x1, y1), (x2, y2) = p, a, b
    if _key(p) in (_key(a), _key(b)):
        return False
    if min(x1, x2) - eps > x or x > max(x1, x2) + eps or min(y1, y2) - eps > y or y > max(y1, y2) + eps:
        return False
    cross = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)
    L = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 or 1
    return abs(cross) / L < eps


def connection_points(doc):
    """every pin and wire vertex -> list of its sources, for junctions and the netlist"""
    wires = [e for e in doc['elements'] if e['type'] == 'wire' and len(e.get('points', [])) >= 2]
    pts = []
    for e in doc['elements']:
        if e['type'] == 'comp' and e['sym'] != 'dot':
            for name, p in pins(e).items():
                pts.append((p, ('pin', e['id'], name)))
    for w in wires:
        P = w['points']
        for i, p in enumerate(P):
            pts.append((tuple(p), ('end' if i in (0, len(P) - 1) else 'mid', w['id'], i)))
    return wires, pts


def junctions(doc):
    wires, pts = connection_points(doc)
    deg: dict = {}
    where: dict = {}
    for p, src in pts:
        k = _key(p)
        where[k] = p
        deg[k] = deg.get(k, 0) + (2 if src[0] == 'mid' else 1)
    for k, p in list(where.items()):
        for w in wires:
            P = w['points']
            for a, b in zip(P, P[1:]):
                if on_segment(p, a, b):
                    deg[k] += 2
    return [where[k] for k, d in deg.items() if d >= 3]


HOP_R = 4


def hops(doc, r=HOP_R):
    """wire id -> {segment index: [crossing points]} where a horizontal wire jumps over a vertical one.
    Only plain crossings hop: a point that is a pin, a wire vertex or a junction is a connection."""
    wires, pts = connection_points(doc)
    conn = {_key(p) for p, _ in pts}
    H, V = [], []
    for w in wires:
        P = w['points']
        for i, (a, b) in enumerate(zip(P, P[1:])):
            if a[1] == b[1] and a[0] != b[0]:
                H.append((w['id'], i, a, b))
            elif a[0] == b[0] and a[1] != b[1]:
                V.append((a, b))
    out: dict = {}
    for wid, i, a, b in H:
        x0, x1, y = min(a[0], b[0]), max(a[0], b[0]), a[1]
        for c, d in V:
            x, y0, y1 = c[0], min(c[1], d[1]), max(c[1], d[1])
            if x0 + r <= x <= x1 - r and y0 < y < y1 and _key((x, y)) not in conn:
                out.setdefault(wid, {}).setdefault(i, []).append((x, y))
    return out


def _n(v):
    v = round(float(v), 2)
    return str(int(v)) if v == int(v) else str(v)


def wire_path(P, hop=None, r=HOP_R):
    """SVG path data for a wire, with a semicircle (bulging up) at each hop on its horizontal segments"""
    d = [f'M{_n(P[0][0])} {_n(P[0][1])}']
    for i, (a, b) in enumerate(zip(P, P[1:])):
        s = 1 if b[0] > a[0] else -1
        for x, y in sorted((hop or {}).get(i, []), key=lambda q: q[0] * s):
            d.append(f'L{_n(x - s * r)} {_n(y)}A{_n(r)} {_n(r)} 0 0 {1 if s > 0 else 0} {_n(x + s * r)} {_n(y)}')
        d.append(f'L{_n(b[0])} {_n(b[1])}')
    return ''.join(d)


def comp_bbox(comp):
    g = geometry(comp)
    x0, y0, x1, y1 = g['bbox']
    a = place(comp, x0, y0); b = place(comp, x1, y1)
    xs = [a[0], b[0]]; ys = [a[1], b[1]]
    for x, y, s, c, an in label_block(comp):
        w = SYM.text_width(s, c)
        lx = x - (w / 2 if an == 'middle' else (w if an == 'end' else 0))
        xs += [lx, lx + w]; ys += [y - 12, y + 3]
    return [min(xs), min(ys), max(xs), max(ys)]


def element_bbox(e):
    t = e['type']
    if t == 'comp':
        return comp_bbox(e)
    if t in ('wire', 'arrow'):
        xs = [p[0] for p in e['points']]; ys = [p[1] for p in e['points']]
        return [min(xs), min(ys), max(xs), max(ys)] if xs else None
    if t == 'rect':
        return [e['x'], e['y'], e['x'] + e['w'], e['y'] + e['h']]
    if t == 'text':
        lines = str(e.get('text', '')).split('\n'); cls = e.get('cls', 'lbl')
        w = max(SYM.text_width(l, cls) for l in lines); a = e.get('anchor', 'start')
        x0 = e['x'] - (w / 2 if a == 'middle' else (w if a == 'end' else 0))
        return [x0, e['y'] - 12, x0 + w, e['y'] + 4 + 16 * (len(lines) - 1)]
    if t == 'raw' and e.get('bbox'):
        b = e['bbox']; return [b[0] + e.get('x', 0), b[1] + e.get('y', 0), b[2] + e.get('x', 0), b[3] + e.get('y', 0)]
    return None


def doc_bbox(doc):
    bs = [b for b in (element_bbox(e) for e in doc['elements']) if b]
    if not bs:
        return [0, 0, 400, 300]
    return [min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs)]
