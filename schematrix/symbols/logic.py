"""Digital logic: buffers and inverters, gates, flip-flops and latches, multiplexers."""
from __future__ import annotations

import math

from .core import ENUM, FLAG, G, Prop, above, below, bez, ci, pg, pl, rc, symbol, tx


def _schmitt(cx, cy, s=4):
    """the hysteresis mark"""
    return pl([(cx - s * 1.5, cy + s / 2), (cx + s / 2, cy + s / 2), (cx + s / 2, cy - s / 2),
               (cx - s / 2, cy - s / 2), (cx - s / 2, cy + s / 2)], 'w thin')


@symbol('buffer', 'Buffer / inverter', 'Logic', 'U', None,
        {'invert': FLAG(False, 'Inverting'), 'size': Prop(22, 'num', True, label='Size'),
         'schmitt': FLAG(False, 'Schmitt trigger'), 'tristate': FLAG(False, 'Tri-state (OE pin)')},
        aliases=('74LS04', '74HC04', '74HC14', 'Buffer', 'Inverter', '74LVC1G04', '74LVC1G125'))
def buffer(p):
    s = float(p['size']); h = s / 2
    prims = [pg([(-h, -h), (-h, h), (h, 0)]), pl([(-h - 10, 0), (-h, 0)])]
    if p['invert']:
        prims += [ci(h + 4, 0, 4, 'pad'), pl([(h + 8, 0), (h + 12, 0)])]
        out = (h + 12, 0)
    else:
        prims.append(pl([(h, 0), (h + 4, 0)]))
        out = (h + 4, 0)
    if p.get('schmitt'):
        prims.append(_schmitt(-h / 3, 0, 3.5))
    pins = {'in': (-h - 10, 0), 'out': out}
    if p.get('tristate'):
        prims.append(pl([(0, -h / 2), (0, -h - 9)])); pins['oe'] = (0, -h - 9)
    return G(prims, pins, below(h + 4))


GATES = ['and', 'nand', 'or', 'nor', 'xor', 'xnor']


@symbol('gate', 'Logic gate', 'Logic', 'U', None,
        {'kind': ENUM('and', GATES, 'Kind'), 'inputs': Prop(2, 'num', True, label='Inputs'),
         'schmitt': FLAG(False, 'Schmitt inputs')},
        aliases=('74LS00', '74HC00', '74LS02', '74HC02', '74LS08', '74HC08', '74LS32', '74HC32', '74LS86', '74HC86'))
def gate(p):
    k = p['kind']; n = max(2, min(6, int(p['inputs'])))
    H = max(15, 5 * n)
    if k in ('and', 'nand'):
        body = [(-20, -H), (5, -H)] + [(5 + H * math.cos(t), H * math.sin(t))
                                        for t in (-math.pi / 2 + math.pi * i / 16 for i in range(17))] + [(5, H), (-20, H)]
        back = lambda y: -20
        prims = [pg(body)]
        tip = 5 + H
    else:
        top = bez((-20, -H), (5, -H), (22, 0)); bot = bez((22, 0), (5, H), (-20, H))
        bk = bez((-20, H), (-10, 0), (-20, -H))
        prims = [pg(top + bot[1:] + bk[1:])]
        back = lambda y: -20 + 20 * ((1 - y / H) / 2) * (1 - (1 - y / H) / 2)
        tip = 22
        if k.startswith('x'):
            prims.append(pl(bez((-26, H), (-16, 0), (-26, -H))))
    ys = [-(H - 5) + 2 * (H - 5) * i / (n - 1) for i in range(n)]
    pins = {}
    for i, y in enumerate(ys, 1):
        prims.append(pl([(-35, y), (back(y) if not k.startswith('x') else back(y) - 6, y)]))
        pins[f'in{i}'] = (-35, y)
    if k in ('nand', 'nor', 'xnor'):
        prims += [ci(tip + 4, 0, 4, 'pad'), pl([(tip + 8, 0), (tip + 13, 0)])]
        pins['out'] = (tip + 13, 0)
    else:
        prims.append(pl([(tip, 0), (tip + 13, 0)])); pins['out'] = (tip + 13, 0)
    if p.get('schmitt'):
        prims.append(_schmitt(0, 0, 4))
    return G(prims, pins, above(-H - 6))


def _overbar(x, y, s, cls='valsm', a='start'):
    """a pin name with a bar over it (active low)"""
    from .core import text_width
    w = text_width(s, cls); x0 = x if a == 'start' else x - w if a == 'end' else x - w / 2
    return [tx(x, y, s, cls, a, ctr=True), pl([(x0, y - 7), (x0 + w, y - 7)], 'w thin')]


FF_PINS = {'d': ['D'], 't': ['T'], 'jk': ['J', 'K'], 'sr': ['S', 'R']}


@symbol('flipflop', 'Flip-flop / latch', 'Logic', 'U', None,
        {'kind': ENUM('d', ['d', 'jk', 't', 'sr', 'd-latch'], 'Kind'), 'set_reset': FLAG(False, 'Async set / reset'),
         'qbar': FLAG(True, 'Q̄ output')},
        aliases=('74LS74', '74HC74', '74LS73', '74HC73', '74HC75', 'DFF', 'D_FlipFlop'))
def flipflop(p):
    k = p['kind']; latch = k == 'd-latch'
    ins = FF_PINS.get('d' if latch else k, ['D'])
    clk = None if k == 'sr' else ('EN' if latch else 'CLK')
    left = ins[:1] + ([clk] if clk else []) + ins[1:]
    H = 20 * len(left) + 10
    y0 = -H / 2
    prims = [rc(-30, y0, 60, H, 'box', 2)]
    pins = {}
    for i, name in enumerate(left):
        y = y0 + 15 + 20 * i
        prims.append(pl([(-40, y), (-30, y)]))
        if name == 'CLK':
            prims += [pl([(-30, y - 5), (-24, y), (-30, y + 5)], 'w thin'), tx(-21, y, 'C', 'valsm', 'start', ctr=True)]
        else:
            prims.append(tx(-26, y, name, 'valsm', 'start', ctr=True))
        pins[name] = (-40, y)
    yq = y0 + 15
    prims += [pl([(30, yq), (40, yq)]), tx(26, yq, 'Q', 'valsm', 'end', ctr=True)]
    pins['Q'] = (40, yq)
    if p['qbar']:
        yn = y0 + H - 15
        prims += [pl([(30, yn), (40, yn)]), *_overbar(26, yn, 'Q', a='end')]
        pins['QN'] = (40, yn)
    if p['set_reset']:
        prims += [ci(0, y0 - 3, 3, 'pad'), pl([(0, y0 - 6), (0, y0 - 10)]), *_overbar(0, y0 + 10, 'S', a='middle'),
                  ci(0, -y0 + 3, 3, 'pad'), pl([(0, -y0 + 6), (0, -y0 + 10)]), *_overbar(0, -y0 - 8, 'R', a='middle')]
        pins.update({'SN': (0, y0 - 10), 'RN': (0, -y0 + 10)})
    return G(prims, pins, above(y0 - (16 if p['set_reset'] else 6)))


@symbol('mux', 'Multiplexer', 'Logic', 'U', None, {'inputs': ENUM(2, [2, 4, 8], 'Inputs')},
        aliases=('74HC157', '74HC153', '74HC151', 'MUX'))
def mux(p):
    n = int(p['inputs']); sel = max(1, int(math.log2(n)))
    step = 20 if n <= 4 else 10
    H = step * (n - 1) / 2 + 15
    slope = 10
    prims = [pg([(-15, -H), (15, -H + slope), (15, H - slope), (-15, H)])]
    pins = {}
    for i in range(n):
        y = (i - (n - 1) / 2) * step
        prims += [pl([(-25, y), (-15, y)]), tx(-12, y, str(i), 'valsm', 'start', ctr=True)]
        pins[f'I{i}'] = (-25, y)
    prims += [pl([(15, 0), (25, 0)])]; pins['Y'] = (25, 0)
    for j in range(sel):
        x = -5 + 10 * j if sel > 1 else 0
        ybot = H - (x + 15) / 30 * slope
        prims.append(pl([(x, ybot), (x, H + 10)])); pins[f'S{j}'] = (x, H + 10)
    return G(prims, pins, above(-H - 6))
