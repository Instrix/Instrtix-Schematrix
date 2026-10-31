"""The rectangular logic-block engine shared by every MSI part (registers, counters, decoders, custom logic ICs).

Pins are given as short specs, the same syntax users type for a custom logic IC:

    'D'      a plain input / output              '~OE'   active low: drawn with an inversion bubble
    '>CLK'   clock: drawn with the clock wedge   'D[8]'  an 8-bit bus: one thick pin with a width slash,
                                                          or eight pins D0..D7 when buses are expanded
Prefixes combine ('~>CLK'); an empty item leaves a gap. Pins sit on a 20-unit pitch (room for pin names inside and
net labels outside), the body on the 5-unit grid.
"""
from __future__ import annotations

import math
import re

from .core import ci, pl, rc, text_width, tx

PITCH = 20
LEAD = 10


def parse(spec: str, bus=True) -> list:
    """'D[8], , >CLK, ~OE' -> pin dicts (None for a gap)"""
    out = []
    for item in str(spec or '').split(','):
        s = item.strip()
        if not s:
            out.append(None)
            continue
        neg = clk = False
        while s[:1] in ('~', '>'):
            neg |= s[0] == '~'; clk |= s[0] == '>'; s = s[1:]
        m = re.match(r'^(.*?)\[(\d+)\]$', s)
        width = int(m.group(2)) if m else 1
        name = (m.group(1) if m else s).strip() or '?'
        out += bus_pins(name, width, bus, neg=neg, clk=clk)
    while out and out[-1] is None:
        out.pop()
    return out


def pin(name, label=None, neg=False, clk=False, width=1):
    return {'name': name, 'label': name if label is None else label, 'neg': neg, 'clk': clk, 'width': width}


def bus_pins(base, n, bus=True, neg=False, clk=False, start=0) -> list:
    """an n-bit port: one bus pin (bus=True), or one pin per bit"""
    n = max(1, int(n))
    if n == 1:
        return [pin(base, neg=neg, clk=clk)]
    if bus:
        return [pin(base, f'{base}[{start + n - 1}:{start}]', neg, clk, n)]
    return [pin(f'{base}{i}', neg=neg, clk=clk) for i in range(start, start + n)]


def _unique(pins_lists):
    seen = {}
    for lst in pins_lists:
        for p in lst:
            if p is None:
                continue
            k = p['name']
            if k in seen:
                seen[k] += 1
                p['name'] = f'{k}_{seen[k]}'
            else:
                seen[k] = 1


def _bus_mark(prims, a, b, width):
    """the slash and bit count across a bus lead from a to b"""
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    if a[1] == b[1]:
        prims += [pl([(mx - 2.5, my + 3.5), (mx + 2.5, my - 3.5)], 'w thin'), tx(mx + 1, my - 6, str(width), 'valsm', 'middle')]
    else:
        prims += [pl([(mx - 3.5, my - 2.5), (mx + 3.5, my + 2.5)], 'w thin'), tx(mx + 6, my + 1, str(width), 'valsm', 'start', ctr=True)]


def _lead(prims, p, edge, end):
    """the lead from the body edge to the pin end, with bubble / bus marks"""
    ux = (end[0] - edge[0]) / LEAD; uy = (end[1] - edge[1]) / LEAD
    start = edge
    if p['neg']:
        prims.append(ci(edge[0] + 3 * ux, edge[1] + 3 * uy, 3, 'pad'))
        start = (edge[0] + 6 * ux, edge[1] + 6 * uy)
    prims.append(pl([start, end], 'w bus' if p['width'] > 1 else 'w'))
    if p['width'] > 1:
        _bus_mark(prims, start, end, p['width'])


def block(title, left, right, top=(), bottom=(), min_w=40):
    """draw a logic block; -> (prims, pins, label). Origin at the body's top-left corner."""
    left, right, top, bottom = list(left), list(right), list(top), list(bottom)
    _unique([left, right, top, bottom])
    lw = lambda ps: max([text_width(p['label'], 'valsm') + (8 if p['clk'] else 0) for p in ps if p] + [0])
    w = max(min_w, text_width(title, 'valsm') + 14 if title else 0, lw(left) + lw(right) + 18,
            PITCH * (len(top) + 1), PITCH * (len(bottom) + 1))
    w = math.ceil(w / 10) * 10
    yt = 10 if top else 0                              # room for top / bottom pin names inside the body
    y0 = (20 if title else 10) + yt
    rows = max(len(left), len(right), 1)
    h = y0 + PITCH * rows + (10 if bottom else 0)
    prims = [rc(0, 0, w, h, 'box', 2)]
    if title:
        prims.append(tx(w / 2, 13 + yt, title, 'valsm', fit=w - 8))
    pins = {}
    for side, lst in (('l', left), ('r', right)):
        for i, p in enumerate(lst):
            if p is None:
                continue
            y = y0 + PITCH * i
            e = 0 if side == 'l' else w
            d = -1 if side == 'l' else 1
            end = (e + d * LEAD, y)
            _lead(prims, p, (e, y), end)
            x = e - d * 4
            if p['clk']:
                prims.append(pl([(e, y - 4), (e - d * 6, y), (e, y + 4)], 'w thin'))
                x -= d * 6
            if p['label']:
                prims.append(tx(x, y, p['label'], 'valsm', 'start' if side == 'l' else 'end', ctr=True))
            pins[p['name']] = end
    for side, lst in (('t', top), ('b', bottom)):
        n = len(lst)
        for i, p in enumerate(lst):
            if p is None:
                continue
            x = w / 2 + PITCH * (i - (n - 1) / 2)
            e = 0 if side == 't' else h
            d = -1 if side == 't' else 1
            end = (x, e + d * LEAD)
            _lead(prims, p, (x, e), end)
            if p['label']:
                prims.append(tx(x, 10 if side == 't' else h - 4, p['label'], 'valsm', 'middle'))
            pins[p['name']] = end
    label = {'x': w / 2, 'y': -6 - (LEAD if top else 0), 'nx': 0, 'ny': -1}
    buses = {p['name']: p['width'] for lst in (left, right, top, bottom) for p in lst if p and p['width'] > 1}
    return prims, pins, label, buses
