"""Sources and sinks: independent and dependent voltage / current sources, batteries, solar cells, current sinks."""
from __future__ import annotations

import math

from .core import ENUM, FLAG, LEN, G, Prop, above, arrow, below, ci, half, leads, light, pg, pl, right, symbol, two_pins, tx


def _circ_src(p):
    h = abs(float(p['length'])) / 2
    return [*leads(h, 16), ci(0, 0, 16, 'amp')], h


V_KINDS = ['dc', 'ac', 'pulse', 'square', 'triangle', 'noise']


@symbol('vsrc', 'Voltage source', 'Sources', 'V', 'V {p} {n} {src}', {'length': LEN(100), 'kind': ENUM('dc', V_KINDS, 'Kind'),
         'text': Prop('', 'str', True, label='Text inside', help='e.g. e_{n}: drawn in the circle instead of the symbol'),
         'signs': FLAG(True, 'Polarity signs')},
        fields=('Amplitude', 'Frequency', 'Offset', 'Output impedance'),
        aliases=('VSOURCE', 'VDC', 'VAC', 'VSIN', 'VPULSE', 'V', 'Voltage_Source'))
def vsrc(p):
    prims, h = _circ_src(p)
    k = p['kind']
    if p.get('text'):                                   # a label in the circle replaces the waveform (and the signs)
        prims.append(tx(0, 0, str(p['text']), 'lbl', ctr=True, fit=26))
        return G(prims, {'p': (-h, 0), 'n': (h, 0)}, above(-24))
    if k == 'ac':
        prims.append(pl([(5 * math.sin(2 * math.pi * i / 20), -9 + 18 * i / 20) for i in range(21)]))
    elif k == 'pulse':
        prims.append(pl([(8, -8), (8, -3), (-6, -3), (-6, 3), (8, 3), (8, 8)]))
    elif k == 'square':
        prims.append(pl([(-9, 4), (-5, 4), (-5, -4), (0, -4), (0, 4), (5, 4), (5, -4), (9, -4)]))
    elif k == 'triangle':
        prims.append(pl([(-9, 3), (-4.5, -4), (0, 3), (4.5, -4), (9, 3)]))
    elif k == 'noise':
        prims.append(pl([(-9, 0), (-7, -5), (-5, 3), (-3, -6), (-1, 4), (1, -3), (3, 6), (5, -4), (7, 2), (9, 0)], 'w thin'))
    if p.get('signs') is False:
        pass
    elif k == 'dc':
        prims += [tx(-7.5, 0, '+', 'pin', ctr=True), tx(7.5, 0, '−', 'pin', ctr=True)]
    else:
        prims.append(tx(-22, -12, '+', 'valsm', ctr=True))     # outside the circle, above the + lead
    return G(prims, {'p': (-h, 0), 'n': (h, 0)}, above(-24))


@symbol('isrc', 'Current source', 'Sources', 'I', 'I {p} {n} {src}',
        {'length': LEN(100), 'text': Prop('', 'str', True, label='Text inside', help='e.g. e_{n}: drawn in the circle instead of the symbol'),
         'arrow_tail': Prop(-10, 'num', True, label='Arrow tail', help='where the arrow starts, from the centre (+ towards n)'),
         'arrow_tip': Prop(10, 'num', True, label='Arrow tip'),
         'arrow_len': Prop(7, 'num', True, label='Arrowhead length'),
         'arrow_w': Prop(4, 'num', True, label='Arrowhead half-width')},
        fields=('Compliance voltage',), aliases=('ISOURCE', 'IDC', 'I', 'Current_Source'))
def isrc(p):
    prims, h = _circ_src(p)
    if p.get('text'):
        prims.append(tx(0, 0, str(p['text']), 'lbl', ctr=True, fit=26))
    else:
        t0, t1 = float(p.get('arrow_tail', -10)), float(p.get('arrow_tip', 10))
        L, W = float(p.get('arrow_len', 7)), float(p.get('arrow_w', 4))
        d = 1 if t1 >= t0 else -1
        prims += [pl([(t0, 0), (t1 - d * min(L * 2 / 7, abs(t1 - t0)), 0)]),
                  pg([(t1 - d * L, -W), (t1 - d * L, W), (t1, 0)], 'arrow')]
    return G(prims, {'p': (-h, 0), 'n': (h, 0)}, above(-24))


@symbol('isink', 'Current sink', 'Sources', 'I', 'I {in} {out} {src}', {'length': LEN(80)},
        fields=('Compliance voltage',), help='drawn vertically: current flows in at the top and out at the bottom',
        aliases=('ISINK', 'Current_Sink'))
def isink(p):
    h = half(p, 80)
    prims = [pl([(0, -h), (0, -14)]), pl([(0, 14), (0, h)]), ci(0, 0, 14, 'amp'), ci(0, 0, 9, 'w thin'),
             *arrow((0, -7.5), (0, 7.5))]
    return G(prims, {'in': (0, -h), 'out': (0, h)}, right(20))


# dependent sources: a diamond, output along x, control terminals above
def _diamond(p, current):
    h = abs(float(p['length'])) / 2
    prims = [*leads(h, 16), pg([(-16, 0), (0, -16), (16, 0), (0, 16)])]
    if current:
        prims += [pl([(-10, 0), (8, 0)]), pg([(3, -4), (3, 4), (10, 0)], 'arrow')]     # centred: -10 .. 10
    else:
        prims += [tx(-7.5, 0, '+', 'pin', ctr=True), tx(7.5, 0, '−', 'pin', ctr=True)]
    return prims, h


def _vcontrolled(p, current):
    prims, h = _diamond(p, current)
    prims += [pl([(-20, -30), (-20, -22)]), pl([(20, -30), (20, -22)]),
              tx(-27, -24, '+', 'valsm', ctr=True), tx(27, -24, '−', 'valsm', ctr=True)]
    return G(prims, {'p': (-h, 0), 'n': (h, 0), 'cp': (-20, -30), 'cn': (20, -30)}, below(24))


def _ccontrolled(p, current):
    prims, h = _diamond(p, current)
    return G(prims, {'p': (-h, 0), 'n': (h, 0)}, above(-22))


DEP = lambda gain: {'length': LEN(100), 'value': Prop(gain, label='Gain')}
CTRL = {'control': Prop('V1', label='Controlling source', help='name of the voltage source whose current controls this one')}


@symbol('vcvs', 'Voltage-controlled V source (E)', 'Sources', 'E', 'E {p} {n} {cp} {cn} {value}', DEP('1'))
def vcvs(p):
    return _vcontrolled(p, False)


@symbol('vccs', 'Voltage-controlled I source (G)', 'Sources', 'G', 'G {p} {n} {cp} {cn} {value}', DEP('1m'))
def vccs(p):
    return _vcontrolled(p, True)


@symbol('ccvs', 'Current-controlled V source (H)', 'Sources', 'H', 'H {p} {n} {ctrl} {value}', {**DEP('1k'), **CTRL})
def ccvs(p):
    return _ccontrolled(p, False)


@symbol('cccs', 'Current-controlled I source (F)', 'Sources', 'F', 'F {p} {n} {ctrl} {value}', {**DEP('1'), **CTRL})
def cccs(p):
    return _ccontrolled(p, True)


@symbol('battery', 'Battery / cell', 'Sources', 'BT', 'V {p} {n} {src}',
        {'length': LEN(40), 'cells': ENUM(1, [1, 2, 3, 4], 'Cells')},
        fields=('Capacity', 'Chemistry', 'Internal resistance'), aliases=('Battery', 'Battery_Cell', 'BAT'))
def battery(p):
    h = abs(float(p['length'])) / 2
    n = int(p.get('cells', 1))
    if n <= 1:
        return G([*leads(h, 3), pl([(-3, -13), (-3, 13)], 'w plate'), pl([(3, -6), (3, 6)], 'w plate'),
                  tx(-10, -12, '+', 'valsm', ctr=True)],
                 {'p': (-h, 0), 'n': (h, 0)}, above(-18))
    w = 10 * n - 4; a = -w / 2
    h = max(h, w / 2 + 8)
    prims = [pl([(-h, 0), (a, 0)]), pl([(-a, 0), (h, 0)]), tx(a - 7, -12, '+', 'valsm', ctr=True)]
    for i in range(n):
        x = a + 10 * i
        prims += [pl([(x, -13), (x, 13)], 'w plate'), pl([(x + 6, -6), (x + 6, 6)], 'w plate')]
        if i < n - 1:
            prims.append(pl([(x + 6, 0), (x + 10, 0)], 'w thin para'))
    return G(prims, {'p': (-h, 0), 'n': (h, 0)}, above(-18))


@symbol('solar', 'Solar cell', 'Sources', 'SC', None, {'length': LEN(40)}, fields=('Voc', 'Isc', 'Power'),
        aliases=('Solar_Cell', 'Solar_Cells'))
def solar(p):
    h = half(p, 40)
    prims = [*leads(h, 3), pl([(-3, -13), (-3, 13)], 'w plate'), pl([(3, -6), (3, 6)], 'w plate'),
             tx(-24, -12, '+', 'valsm', ctr=True), ci(0, 0, 17, 'w thin'), *light(8, -22, inward=True, ang=-60)]
    return G(prims, {'p': (-h, 0), 'n': (h, 0)}, below(24))


@symbol('generator', 'Generator / alternator', 'Sources', 'G', None, {'length': LEN(100), 'letter': Prop('G', 'str', True, label='Letter')},
        aliases=('Generator', 'Generator_AC', 'Generator_DC'))
def generator(p):
    prims, h = _circ_src(p)
    prims.append(tx(0, 0, str(p['letter']), 'ref', ctr=True, fit=24))
    return G(prims, two_pins(h), above(-24))

