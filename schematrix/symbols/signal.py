"""Signal-flow blocks: amplifiers, summing junctions, mixers, oscillators, filters, converters."""
from __future__ import annotations

import math

from .core import ENUM, FLAG, G, Prop, above, ci, pg, pl, rc, symbol, tx


@symbol('amplifier', 'Amplifier (block)', 'Signal flow', 'A', None,
        {'gain': Prop('', 'str', True, label='Text inside', help='e.g. ×10, G, 20 dB'), 'size': Prop(40, 'num', True, label='Size')},
        fields=('Gain', 'Bandwidth'))
def amplifier(p):
    s = float(p['size']); h = s / 2
    prims = [pg([(-h, -h), (-h, h), (h, 0)]), pl([(-h - 10, 0), (-h, 0)]), pl([(h, 0), (h + 10, 0)])]
    if p['gain']:
        prims.append(tx(-h / 3, 0, str(p['gain']), 'valsm', ctr=True))
    return G(prims, {'in': (-h - 10, 0), 'out': (h + 10, 0)}, above(-h - 6))


@symbol('summer', 'Summing junction', 'Signal flow', 'S', None,
        {'signs': Prop('++', 'str', True, label='Signs', help='sign of the left and bottom inputs, e.g. +- '),
         'mark': ENUM('Σ', ['Σ', '+', 'none'], 'Mark')})
def summer(p):
    r = 12
    prims = [ci(0, 0, r, 'amp'), pl([(-25, 0), (-r, 0)]), pl([(0, r), (0, 25)]), pl([(r, 0), (25, 0)])]
    if p['mark'] != 'none':
        prims.append(tx(0, 0, p['mark'], 'pin', ctr=True))
    signs = (str(p['signs']) + '++')[:2]
    prims += [tx(-18, -8, signs[0].replace('-', '−'), 'valsm', ctr=True), tx(8, 19, signs[1].replace('-', '−'), 'valsm', ctr=True)]
    return G(prims, {'in1': (-25, 0), 'in2': (0, 25), 'out': (25, 0)}, above(-18))


@symbol('mixer', 'Mixer / multiplier', 'Signal flow', 'MX', None, {}, aliases=('Mixer',))
def mixer(p):
    r = 12; d = r * 0.707
    prims = [ci(0, 0, r, 'amp'), pl([(-d, -d), (d, d)]), pl([(-d, d), (d, -d)]),
             pl([(-25, 0), (-r, 0)]), pl([(0, r), (0, 25)]), pl([(r, 0), (25, 0)])]
    return G(prims, {'rf': (-25, 0), 'lo': (0, 25), 'if': (25, 0)}, above(-18))


@symbol('oscillator', 'Oscillator', 'Signal flow', 'X', None, {}, fields=('Frequency', 'Stability'), aliases=('Oscillator',))
def oscillator(p):
    r = 14
    prims = [ci(0, 0, r, 'amp'), pl([(-8 + 16 * i / 20, -5 * math.sin(2 * math.pi * i / 20)) for i in range(21)]),
             pl([(r, 0), (25, 0)])]
    return G(prims, {'out': (25, 0)}, above(-20))


@symbol('filter', 'Filter (block)', 'Signal flow', 'FL', None,
        {'kind': ENUM('lp', ['lp', 'hp', 'bp', 'bs'], 'Response')}, fields=('Cut-off', 'Order', 'Type'), aliases=('Filter',))
def filter_(p):
    k = p['kind']
    prims = [rc(-20, -15, 40, 30, 'box', 2), pl([(-30, 0), (-20, 0)]), pl([(20, 0), (30, 0)])]
    wave = lambda y: [(-10 + 20 * i / 16, y - 2.5 * math.sin(2 * math.pi * i / 8)) for i in range(17)]
    ys = (-7, 0, 7)
    struck = {'lp': (0,), 'hp': (2,), 'bp': (0, 2), 'bs': (1,)}[k]
    for i, y in enumerate(ys):
        prims.append(pl(wave(y), 'w thin'))
        if i in struck:
            prims.append(pl([(-6, y + 4), (6, y - 4)]))
    return G(prims, {'in': (-30, 0), 'out': (30, 0)}, above(-21))


@symbol('converter', 'Converter (ADC / DAC / DC-DC)', 'Signal flow', 'U', None,
        {'src': Prop('A', 'str', True, label='From'), 'dst': Prop('D', 'str', True, label='To'),
         'isolated': FLAG(False, 'Isolated')},
        fields=('Resolution', 'Sample rate', 'Efficiency'))
def converter(p):
    prims = [rc(-20, -20, 40, 40, 'box', 2), pl([(-20, 20), (20, -20)], 'w thin'),
             tx(-10, -8, str(p['src']), 'valsm', ctr=True), tx(10, 9, str(p['dst']), 'valsm', ctr=True),
             pl([(-30, 0), (-20, 0)]), pl([(20, 0), (30, 0)])]
    if p['isolated']:
        prims.append(pl([(0, -26), (0, 26)], 'w para'))
    return G(prims, {'in': (-30, 0), 'out': (30, 0)}, above(-26))


@symbol('attenuator', 'Attenuator / pad', 'Signal flow', 'AT', None, {}, fields=('Attenuation', 'Impedance'))
def attenuator(p):
    prims = [rc(-15, -12, 30, 24, 'box', 2), tx(0, 0, 'dB', 'valsm', ctr=True), pl([(-25, 0), (-15, 0)]), pl([(15, 0), (25, 0)])]
    return G(prims, {'in': (-25, 0), 'out': (25, 0)}, above(-18))

