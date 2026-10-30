"""Netlist -> schematic: place the parts in rows and give every connected pin a short stub with a net label
(or a ground symbol), so the drawing has exactly the netlist's connectivity and can be tidied by hand."""
from __future__ import annotations

import re

from .. import geometry as GEO
from .. import symbols as SYM
from .model import Netlist, Part, is_ground

STUB, GAP, ROW_GAP, MAX_W = 20, 40, 50, 1100
SIDES = {'l': (-1, 0), 'r': (1, 0), 't': (0, -1), 'b': (0, 1)}


def _snap(v, g=5):
    return round(v / g) * g


def _side(pt, bbox, prims=()) -> str:
    """which way a pin faces: along the lead that ends on it, else towards the nearest bbox edge"""
    x, y = pt
    for p in prims:
        if p['k'] != 'pl':
            continue
        P = p['pts']
        for end, nxt in ((P[0], P[1] if len(P) > 1 else None), (P[-1], P[-2] if len(P) > 1 else None)):
            if nxt and abs(end[0] - x) < 0.01 and abs(end[1] - y) < 0.01:
                dx, dy = x - nxt[0], y - nxt[1]
                if abs(dx) > abs(dy):
                    return 'r' if dx > 0 else 'l'
                if abs(dy) > abs(dx):
                    return 'b' if dy > 0 else 't'
    x0, y0, x1, y1 = bbox
    d = {'l': x - x0, 'r': x1 - x, 't': y - y0, 'b': y1 - y}
    return min(('l', 'r', 't', 'b'), key=lambda k: (d[k], k in 'tb'))


def _label_w(net) -> float:
    return STUB + 17 + 7.2 * len(str(net))


def _as_block(p: Part) -> Part:
    names = list(p.pins)
    k = len(names)
    spec = ', '.join(f'{n}:{"l" if i < (k + 1) // 2 else "r"}' for i, n in enumerate(names))
    return Part(p.ref, 'block', p.value, p.part, {'title': p.lib or p.sym or p.ref, 'pins': spec, 'w': 100,
                                                    'h': max(40, 20 * ((k + 1) // 2) + 10)}, p.fields, p.pins, p.lib)


def _auto(net) -> bool:
    return bool(re.fullmatch(r'N\d+|N\$\d+|net\d*|\?', str(net)))


def to_schematic(nl: Netlist, title=None):
    from ..document import Schematic
    s = Schematic(title or nl.title or 'Imported netlist')
    nets = nl.nets()
    x = y = rowh = 0
    for p in nl.parts:
        if p.sym not in SYM.REGISTRY:
            p = _as_block(p)
        sym = SYM.get(p.sym)
        known = sym.all_props()
        props = {k: v for k, v in p.props.items() if k in known and k not in ('ref', 'value', 'part')}
        c = s.add(p.sym, (0, 0), ref=p.ref, value=p.value or None, part=p.part or None, fields=p.fields or None, **props)
        g = GEO.geometry(c.el)
        bb = g['bbox']
        missing = [pin for pin in p.pins if pin not in g['pins']]
        if missing:
            nl.warnings.append(f'{p.ref}: {sym.name} has no pins {", ".join(missing)}')
        labelled = {pin: net for pin, net in p.pins.items()
                    if pin in g['pins'] and net not in ('', '?') and not (len(nets.get(net, ())) < 2 and _auto(net))}
        side = {pin: _side(g['pins'][pin], bb, g['prims']) for pin in labelled}
        L = max([_label_w(n) for pin, n in labelled.items() if side[pin] == 'l'] + [0])
        R = max([_label_w(n) for pin, n in labelled.items() if side[pin] == 'r'] + [0])
        T = 35 if any(v == 't' for v in side.values()) else 0
        B = 40 if any(v == 'b' for v in side.values()) else 0
        w = L + (bb[2] - bb[0]) + R
        if x and x + w > MAX_W:
            x, y, rowh = 0, y + rowh + ROW_GAP, 0
        c.moveto(_snap(x + L - bb[0]), _snap(y + T - bb[1]))
        for pin, net in labelled.items():
            pt = c[pin]; dx, dy = SIDES[side[pin]]
            end = (pt[0] + dx * STUB, pt[1] + dy * STUB)
            s.wire(pt, end)
            if is_ground(net):
                s.add('ground', end, 180 if side[pin] == 't' else 0, net=net)
            else:
                s.flag(end, str(net), side='left' if side[pin] == 'l' else 'right')
        x += w + GAP
        rowh = max(rowh, T + (bb[3] - bb[1]) + B)
    return s
