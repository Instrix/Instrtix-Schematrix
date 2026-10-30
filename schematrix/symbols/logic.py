"""Digital logic: gates, buffers and inverters, flip-flops and latches, multiplexers.
Larger blocks (registers, counters, decoders, ...) are in digital.py."""
from __future__ import annotations

import math

from .core import ENUM, FLAG, G, Prop, above, below, bez, ci, pg, pl, rc, symbol, text_width, tx
from .logic_block import _bus_mark


def _schmitt(cx, cy, s=4):
    """the hysteresis mark: a low line entering from the left that rises on the right, and a high line leaving to
    the right that falls on the left — two overlapping steps"""
    a, h = s / 2, s * 0.6
    return [pl([(cx - 3 * a, cy + h), (cx + a, cy + h), (cx + a, cy - h)], 'w thin'),
            pl([(cx + 3 * a, cy - h), (cx - a, cy - h), (cx - a, cy + h)], 'w thin')]


def _inverted(spec, n) -> set:
    """'1, 3' / 'all' -> {1, 3} (1-based input numbers)"""
    s = str(spec or '').strip().lower()
    if s in ('all', '*'):
        return set(range(1, n + 1))
    return {int(t) for t in s.replace(';', ',').split(',') if t.strip().isdigit()}


SHAPE = ENUM('ansi', ['ansi', 'iec'], 'Shape', help='ansi: distinctive shapes; iec: rectangles with &, ≥1, =1, 1')


@symbol('buffer', 'Buffer / inverter', 'Logic', 'U', None,
        {'invert': FLAG(False, 'Inverting'), 'size': Prop(22, 'num', True, label='Size'),
         'schmitt': FLAG(False, 'Schmitt trigger'), 'tristate': FLAG(False, 'Tri-state (OE pin)'),
         'shape': SHAPE},
        aliases=('Buffer', 'Inverter'),
        presets=(('buffer_gate', 'Buffer', {}, ('74LVC1G34', '74HC244', '74HC541')),
                 ('not_gate', 'NOT gate (inverter)', {'invert': True}, ('74HC04', '74LS04', '74LVC1G04', '74AHC1G04', 'NOT')),
                 ('schmitt_inverter', 'Schmitt inverter', {'invert': True, 'schmitt': True}, ('74HC14', '74LS14', '74LVC1G14')),
                 ('schmitt_buffer', 'Schmitt buffer', {'schmitt': True}, ('74LVC1G17',)),
                 ('tristate_buffer', 'Tri-state buffer', {'tristate': True}, ('74HC125', '74LVC1G125', '74HC126'))))
def buffer(p):
    if p.get('shape') == 'iec':
        prims = [rc(-10, -10, 20, 20, 'box', 1), tx(0, -5 if p.get('schmitt') else 0, '1', 'valsm', ctr=True),
                 pl([(-20, 0), (-10, 0)])]
        if p['invert']:
            prims += [ci(13, 0, 3, 'pad'), pl([(16, 0), (20, 0)])]
        else:
            prims.append(pl([(10, 0), (20, 0)]))
        if p.get('schmitt'):
            prims += _schmitt(0, 5, 3.5)
        pins = {'in': (-20, 0), 'out': (20, 0)}
        if p.get('tristate'):
            prims += [pl([(0, -10), (0, -20)]), tx(-3, -16, 'EN', 'valsm', 'end', ctr=True)]
            pins['oe'] = (0, -20)
        return G(prims, pins, below(14))
    s = float(p['size']); h = s / 2
    prims = [pg([(-h, -h), (-h, h), (h, 0)]), pl([(-h - 10, 0), (-h, 0)])]
    if p['invert']:
        prims += [ci(h + 4, 0, 4, 'pad'), pl([(h + 8, 0), (h + 12, 0)])]
        out = (h + 12, 0)
    else:
        prims.append(pl([(h, 0), (h + 4, 0)]))
        out = (h + 4, 0)
    if p.get('schmitt'):
        prims += _schmitt(-h / 3, 0, 4.5)
    pins = {'in': (-h - 10, 0), 'out': out}
    if p.get('tristate'):
        prims.append(pl([(0, -h / 2), (0, -h - 9)])); pins['oe'] = (0, -h - 9)
    return G(prims, pins, below(h + 4))


GATES = ['and', 'nand', 'or', 'nor', 'xor', 'xnor']
IEC_MARK = {'and': '&', 'nand': '&', 'or': '≥1', 'nor': '≥1', 'xor': '=1', 'xnor': '=1'}
GATE_PRESETS = (
    ('and_gate', 'AND gate', {}, ('74HC08', '74LS08', '74LVC1G08', 'AND')),
    ('nand_gate', 'NAND gate', {'kind': 'nand'}, ('74HC00', '74LS00', '74LVC1G00', '74HC132', 'NAND')),
    ('or_gate', 'OR gate', {'kind': 'or'}, ('74HC32', '74LS32', '74LVC1G32', 'OR')),
    ('nor_gate', 'NOR gate', {'kind': 'nor'}, ('74HC02', '74LS02', '74LVC1G02', 'NOR')),
    ('xor_gate', 'XOR gate', {'kind': 'xor'}, ('74HC86', '74LS86', '74LVC1G86', 'XOR')),
    ('xnor_gate', 'XNOR gate', {'kind': 'xnor'}, ('74HC7266', '74LVC1G386', 'XNOR')),
)


@symbol('gate', 'Logic gate', 'Logic', 'U', None,
        {'kind': ENUM('and', GATES, 'Kind'), 'inputs': Prop(2, 'num', True, label='Inputs', help='2 to 16'),
         'invert_inputs': Prop('', 'str', True, label='Inverted inputs', help='input numbers with a bubble, e.g. "1, 3" or "all"'),
         'shape': SHAPE, 'schmitt': FLAG(False, 'Schmitt inputs')},
        presets=GATE_PRESETS)
def gate(p):
    k = p['kind']; n = max(2, min(16, int(float(p['inputs']))))
    inv = _inverted(p.get('invert_inputs'), n)
    neg_out = k in ('nand', 'nor', 'xnor')
    if p.get('shape') == 'iec':
        step = 20 if n == 2 else 10
        H = max(30, step * (n - 1) + 20)
        prims = [rc(-15, -H / 2, 30, H, 'box', 1), tx(0, -H / 2 + 12, IEC_MARK[k], 'valsm')]
        pins = {}
        for i in range(n):
            y = (i - (n - 1) / 2) * step
            if i + 1 in inv:
                prims += [ci(-18, y, 3, 'pad'), pl([(-25, y), (-21, y)])]
            else:
                prims.append(pl([(-25, y), (-15, y)]))
            pins[f'in{i + 1}'] = (-25, y)
        prims += [ci(18, 0, 3, 'pad'), pl([(21, 0), (25, 0)])] if neg_out else [pl([(15, 0), (25, 0)])]
        pins['out'] = (25, 0)
        if p.get('schmitt'):
            prims += _schmitt(0, -H / 2 + 24, 5)
        return G(prims, pins, above(-H / 2 - 6))
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
        bx = back(y) if not k.startswith('x') else back(y) - 6
        if i in inv:
            prims += [ci(bx - 4, y, 4, 'pad'), pl([(-35, y), (bx - 8, y)])]
        else:
            prims.append(pl([(-35, y), (bx, y)]))
        pins[f'in{i}'] = (-35, y)
    if neg_out:
        prims += [ci(tip + 4, 0, 4, 'pad'), pl([(tip + 8, 0), (tip + 13, 0)])]
        pins['out'] = (tip + 13, 0)
    else:
        prims.append(pl([(tip, 0), (tip + 13, 0)])); pins['out'] = (tip + 13, 0)
    if p.get('schmitt'):
        prims += _schmitt(-2, 0, 6)
    return G(prims, pins, above(-H - 6))


def _overbar(x, y, s, cls='valsm', a='start'):
    """a pin name with a bar over it (active low)"""
    w = text_width(s, cls); x0 = x if a == 'start' else x - w if a == 'end' else x - w / 2
    return [tx(x, y, s, cls, a, ctr=True), pl([(x0, y - 7), (x0 + w, y - 7)], 'w thin')]


FF_PINS = {'d': ['D'], 't': ['T'], 'jk': ['J', 'K'], 'sr': ['S', 'R']}


@symbol('flipflop', 'Flip-flop / latch', 'Logic', 'U', None,
        {'kind': ENUM('d', ['d', 'jk', 't', 'sr', 'd-latch'], 'Kind'), 'set_reset': FLAG(False, 'Async set / reset'),
         'qbar': FLAG(True, 'Q̄ output')},
        aliases=('DFF', 'D_FlipFlop'),
        presets=(('dff', 'D flip-flop', {}, ('74HC74', '74LS74', '74AHC1G79', 'D_FlipFlop')),
                 ('dff_sr', 'D flip-flop, set / reset', {'set_reset': True}, ('74HC74_SR',)),
                 ('jkff', 'JK flip-flop', {'kind': 'jk'}, ('74HC73', '74LS73', '74HC107', '74HC109')),
                 ('tff', 'T flip-flop', {'kind': 't'}),
                 ('sr_latch', 'SR latch', {'kind': 'sr'}, ('74HC279', '74LS279')),
                 ('d_latch', 'D latch', {'kind': 'd-latch'}, ('74HC75', '74LS75'))))
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


@symbol('mux', 'Multiplexer', 'Logic', 'U', None,
        {'inputs': ENUM(2, [2, 4, 8, 16], 'Inputs'), 'width': Prop(1, 'num', True, label='Data width', help='bits per input (bus)'),
         'enable': FLAG(False, 'Enable pin')},
        aliases=('MUX',),
        presets=(('mux2', 'Multiplexer 2:1', {}, ('74HC157', '74LVC1G157')),
                 ('mux4', 'Multiplexer 4:1', {'inputs': 4}, ('74HC153',)),
                 ('mux8', 'Multiplexer 8:1', {'inputs': 8}, ('74HC151',)),
                 ('mux16', 'Multiplexer 16:1', {'inputs': 16}, ('74HC150', 'CD74HC4067'))))
def mux(p):
    n = int(p['inputs']); sel = max(1, int(math.log2(n)))
    width = max(1, int(float(p.get('width', 1))))
    step = 20 if n <= 4 else 10
    H = step * (n - 1) / 2 + 15
    a = 15 if sel <= 3 else 20               # half width: room for the select lines
    slope = 10
    prims = [pg([(-a, -H), (a, -H + slope), (a, H - slope), (-a, H)])]
    lead = 'w bus' if width > 1 else 'w'
    pins = {}
    for i in range(n):
        y = (i - (n - 1) / 2) * step
        prims += [pl([(-a - 10, y), (-a, y)], lead), tx(-a + 3, y, str(i), 'valsm', 'start', ctr=True)]
        pins[f'I{i}'] = (-a - 10, y)
    prims.append(pl([(a, 0), (a + 10, 0)], lead)); pins['Y'] = (a + 10, 0)
    if width > 1:
        _bus_mark(prims, (a, 0), (a + 10, 0), width)
    for j in range(sel):
        x = 0 if sel == 1 else 10 * (j - (sel - 1) / 2)
        ybot = H - (x + a) / (2 * a) * slope
        prims.append(pl([(x, ybot), (x, H + 10)])); pins[f'S{j}'] = (x, H + 10)
    if p.get('enable'):
        ytop = -H + slope / 2
        prims += [ci(0, ytop - 3, 3, 'pad'), pl([(0, ytop - 6), (0, -H - 10)])]
        pins['EN'] = (0, -H - 10)
    return G(prims, pins, above(-H - (16 if p.get('enable') else 6)))
