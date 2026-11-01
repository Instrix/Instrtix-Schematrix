"""Automatic wire routing: an orthogonal path between two points that goes around parts.

    pts = route(doc, (100, 50), (300, 120))          # [(x, y), ...] on the sheet grid

A* over the grid with a cost for every bend. Part bodies and other pins are walls (crossing a pin would connect
to it); running along another wire costs a lot (it would look connected), crossing one costs a little, and so do
labels and texts. Falls back to a simple dog-leg when no path exists inside the search area.
"""
from __future__ import annotations

import heapq

from . import geometry as GEO
from . import symbols as SYM

BEND, ALONG, CROSS, LABEL, CLEAR = 12.0, 40.0, 2.0, 30.0, 8.0
MARGIN = 60               # how far around the drawing the search may go
MAX_NODES = 400_000


def _body(comp):
    x0, y0, x1, y1 = GEO.geometry(comp)['bbox']
    a, b = GEO.place(comp, x0, y0), GEO.place(comp, x1, y1)
    return min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])


def _labels(doc):
    out = []
    for e in doc['elements']:
        if e['type'] == 'comp':
            for x, y, s, c, an in GEO.label_block(e):
                w = SYM.text_width(s, c)
                lx = x - (w / 2 if an == 'middle' else (w if an == 'end' else 0))
                out.append((lx, y - 11, lx + w, y + 2))
        elif e['type'] == 'text':
            b = GEO.element_bbox(e)
            if b:
                out.append(tuple(b))
    return out


def route(doc, a, b, ignore=(), grid=None):
    """an orthogonal polyline from a to b avoiding the sheet's parts; ignore: element ids to leave out (the wire
    being re-routed)"""
    g = float(grid or doc.get('page', {}).get('grid') or 5)
    snap = lambda v: round(v / g) * g
    a, b = (float(a[0]), float(a[1])), (float(b[0]), float(b[1]))
    A, B = (snap(a[0]), snap(a[1])), (snap(b[0]), snap(b[1]))
    ignore = set(ignore)
    els = [e for e in doc['elements'] if e.get('id') not in ignore]
    comps = [e for e in els if e['type'] == 'comp' and e.get('sym') not in ('dot',)]
    bodies = [_body(c) for c in comps if not SYM.get(c['sym']).category == 'Annotation']
    labels = _labels({'elements': els})
    ends = {A, B}
    pins = {(snap(x), snap(y)) for c in comps for x, y in GEO.pins(c).values()} - ends
    wires = [e for e in els if e['type'] == 'wire' and len(e.get('points', [])) >= 2]
    tips = {(snap(p[0]), snap(p[1])) for w in wires for p in (w['points'][0], w['points'][-1])} - ends
    along = set()                                       # grid edges covered by existing wires
    on_wire = set()
    for w in wires:
        for p, q in zip(w['points'], w['points'][1:]):
            p, q = (snap(p[0]), snap(p[1])), (snap(q[0]), snap(q[1]))
            if p[0] == q[0] or p[1] == q[1]:
                n = int(round(max(abs(q[0] - p[0]), abs(q[1] - p[1])) / g))
                dx, dy = (q[0] - p[0]) / (n or 1), (q[1] - p[1]) / (n or 1)
                pts = [(p[0] + dx * i, p[1] + dy * i) for i in range(n + 1)]
                on_wire.update(pts)
                along.update(frozenset(e) for e in zip(pts, pts[1:]))
    xs = [x for bb in bodies for x in (bb[0], bb[2])] + [A[0], B[0]]
    ys = [y for bb in bodies for y in (bb[1], bb[3])] + [A[1], B[1]]
    X0, X1 = snap(min(xs) - MARGIN), snap(max(xs) + MARGIN)
    Y0, Y1 = snap(min(ys) - MARGIN), snap(max(ys) + MARGIN)

    def blocked(p):
        if p in ends:
            return False
        if p in pins or p in tips:
            return True
        return any(bb[0] < p[0] < bb[2] and bb[1] < p[1] < bb[3] for bb in bodies)

    def label_cost(p):
        c = LABEL if any(lb[0] <= p[0] <= lb[2] and lb[1] <= p[1] <= lb[3] for lb in labels) else 0.0
        if p not in ends and any(bb[0] - g <= p[0] <= bb[2] + g and bb[1] - g <= p[1] <= bb[3] + g for bb in bodies):
            c += CLEAR                                  # keep a grid step away from bodies (pins sit on their edges)
        return c

    h = lambda p: abs(p[0] - B[0]) + abs(p[1] - B[1])
    dirs = [(g, 0), (-g, 0), (0, g), (0, -g)]
    start = (A, None)
    best = {start: 0.0}
    came = {}
    heap = [(h(A), 0.0, A, None)]
    seen = 0
    while heap:
        f, cost, p, d = heapq.heappop(heap)
        if p == B:
            path = [p]
            key = (p, d)
            while key in came:
                key = came[key]
                path.append(key[0])
            return _simplify([a] + path[::-1][1:-1] + [b] if path[-1] == A else [a, b])
        if cost > best.get((p, d), float('inf')):
            continue
        seen += 1
        if seen > MAX_NODES:
            break
        for nd in dirs:
            q = (p[0] + nd[0], p[1] + nd[1])
            if not (X0 <= q[0] <= X1 and Y0 <= q[1] <= Y1) or blocked(q):
                continue
            c = cost + g + (BEND if d is not None and nd != d else 0.0)
            if frozenset((p, q)) in along:
                c += ALONG
            elif q in on_wire and q not in ends:
                c += CROSS
            c += label_cost(q)
            if c < best.get((q, nd), float('inf')):
                best[(q, nd)] = c
                came[(q, nd)] = (p, d)
                heapq.heappush(heap, (c + h(q), c, q, nd))
    mid = (B[0], A[1])                                   # no way round: a plain dog-leg
    return _simplify([a, mid, b])


def _simplify(pts):
    """drop repeated and collinear points"""
    out = []
    for p in pts:
        p = (round(p[0], 2), round(p[1], 2))
        if out and p == out[-1]:
            continue
        if len(out) >= 2:
            (x0, y0), (x1, y1) = out[-2], out[-1]
            if (x0 == x1 == p[0]) or (y0 == y1 == p[1]):
                out[-1] = p
                continue
        out.append(p)
    return out
