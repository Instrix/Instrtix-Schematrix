"""Loads and meters: lamps, motors, heaters, speakers, buzzers, microphones, electronic loads, measuring instruments."""
from __future__ import annotations

import math

from .core import ENUM, LEN, G, Prop, above, ci, half, leads, pg, pl, rc, symbol, two_pins, tx


@symbol('lamp', 'Lamp', 'Loads & meters', 'LA', None, {'length': LEN(60)}, fields=('Voltage', 'Power'),
        aliases=('Lamp', 'Lamp_Small'))
def lamp(p):
    h = half(p)
    d = 9.9
    return G([*leads(h, 14), ci(0, 0, 14, 'amp'), pl([(-d, -d), (d, d)]), pl([(-d, d), (d, -d)])], two_pins(h), above(-20))


@symbol('motor', 'Motor', 'Loads & meters', 'M', None,
        {'length': LEN(60), 'kind': ENUM('dc', ['dc', 'ac', 'stepper'], 'Kind')}, fields=('Voltage', 'Current', 'Speed'),
        aliases=('Motor_DC', 'Motor_AC', 'Motor', 'Fan'))
def motor(p):
    h = half(p)
    prims = [*leads(h, 15), ci(0, 0, 15, 'amp'), tx(0, -1, 'M', 'ref', ctr=True)]
    if p['kind'] == 'ac':
        prims.append(pl([(-5 + i, 8 - 2.5 * math.sin(i / 10 * 2 * math.pi)) for i in range(11)], 'w thin'))
    elif p['kind'] == 'stepper':
        prims.append(pl([(-5, 9), (-2, 9), (-2, 6), (2, 6), (2, 9), (5, 9)], 'w thin'))
    else:
        prims.append(pl([(-5, 8), (5, 8)], 'w thin'))
    return G(prims, two_pins(h), above(-21))


@symbol('heater', 'Heater', 'Loads & meters', 'HE', 'R {1} {2} {value}', {'length': LEN(60)}, fields=('Power', 'Voltage'),
        aliases=('Heater',))
def heater(p):
    h = half(p)
    prims = [*leads(h, 16), pl([(-16, -7), (16, -7), (16, 7), (-16, 7), (-16, -7)])]
    prims += [pl([(x, -7), (x, 7)], 'w thin') for x in (-8, 0, 8)]
    return G(prims, two_pins(h), above(-13))


@symbol('speaker', 'Loudspeaker', 'Loads & meters', 'LS', None, {}, fields=('Impedance', 'Power'),
        aliases=('Speaker', 'Speaker_Crystal'))
def speaker(p):
    prims = [rc(-6, -10, 8, 20, 'box', 1), pg([(2, -10), (14, -20), (14, 20), (2, 10)]),
             pl([(-20, -5), (-6, -5)]), pl([(-20, 5), (-6, 5)])]
    return G(prims, {'1': (-20, -5), '2': (-20, 5)}, above(-26))


@symbol('buzzer', 'Buzzer / piezo', 'Loads & meters', 'BZ', None, {'length': LEN(60)}, fields=('Voltage', 'Frequency'),
        aliases=('Buzzer', 'Speaker_Crystal'))
def buzzer(p):
    h = half(p)
    dome = [(12 * math.cos(math.radians(a)), -12 * math.sin(math.radians(a))) for a in range(0, 181, 15)]
    prims = [pl([(-h, 0), (-12, 0)]), pl([(12, 0), (h, 0)]), pg(dome)]
    return G(prims, two_pins(h), above(-17))


@symbol('microphone', 'Microphone', 'Loads & meters', 'MK', None, {}, fields=('Sensitivity', 'Bias'),
        aliases=('Microphone', 'Microphone_Condenser'))
def microphone(p):
    prims = [ci(0, 0, 12, 'amp'), pl([(-12, -12), (-12, 12)], 'w plate'),
             pl([(0, 12), (0, 20)]), pl([(0, -12), (0, -20)])]
    return G(prims, {'1': (0, -20), '2': (0, 20)}, {'x': 18, 'y': 0, 'nx': 1, 'ny': 0})


@symbol('load', 'Electronic load', 'Loads & meters', 'RL', None, {'length': LEN(60), 'label': Prop('LOAD', label='Label')},
        fields=('Mode', 'Setpoint', 'Power'), help='a generic load or DUT drawn as a box')
def load(p):
    h = half(p)
    return G([*leads(h, 20), rc(-20, -10, 40, 20, 'box', 2), tx(0, 0, str(p['label']), 'valsm', ctr=True, fit=36)],
             two_pins(h), above(-16))


METERS = ['V', 'A', 'Ω', 'W', 'Hz', 'mV', 'mA', 'µA', 'G', 'T']


@symbol('meter', 'Meter (V / A / Ω / W …)', 'Loads & meters', 'M',
        None, {'length': LEN(60), 'letter': Prop('V', 'enum', True, METERS + ['Osc'], 'Quantity')},
        fields=('Range', 'Accuracy'), aliases=('Voltmeter_DC', 'Ammeter_DC', 'Voltmeter_AC', 'Ammeter_AC', 'Meter'))
def meter(p):
    h = half(p)
    s = str(p['letter'])
    prims = [*leads(h, 14), ci(0, 0, 14, 'amp')]
    if s == 'Osc':
        prims += [rc(-9, -7, 18, 14, 'w thin', 1), pl([(-7, 2), (-4, -3), (-1, 2), (2, -3), (5, 2), (7, -1)], 'w thin')]
    else:
        prims.append(tx(0, 0, s, 'ref' if len(s) <= 2 else 'valsm', ctr=True, fit=22))
    return G(prims, two_pins(h), above(-20))


@symbol('probe', 'Test probe / scope tip', 'Loads & meters', 'TP', None, {}, help='a probe touching a net; one pin')
def probe(p):
    return G([pl([(0, 0), (0, -6)]), pg([(-3, -6), (3, -6), (3, -24), (-3, -24)], 'box'), pl([(0, -24), (0, -30)], 'w thin')],
             {'p': (0, 0)}, {'x': 8, 'y': -18, 'nx': 1, 'ny': 0})

