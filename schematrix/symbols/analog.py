"""Analog ICs: op-amps and comparators, instrumentation amplifiers, regulators, voltage references."""
from __future__ import annotations

from .core import ENUM, FLAG, G, Prop, above, pg, pl, rc, right, symbol, tx


@symbol('opamp', 'Op-amp', 'Analog', 'U', 'X {inp} {inm} {vp?} {vn?} {out} {model}',
        {'top': ENUM('-', ['-', '+'], 'Top input'), 'supply': FLAG(False, 'Supply pins'),
         'comparator': FLAG(False, 'Comparator', help='draws the step mark')},
        model=lambda p: 'OPAMP5' if p.get('supply') else 'OPAMP', fields=('GBW', 'Slew rate', 'Supply range', 'Offset'),
        pin_numbers={'out': '1', 'inm': '2', 'inp': '3', 'vn': '4', 'vp': '8'},
        aliases=('Opamp_Dual', 'Opamp', 'OPAMP', 'LM358', 'TL072', 'Comparator', 'LM393'))
def opamp(p):
    top = p['top']
    prims = [pg([(-30, -32), (-30, 32), (32, 0)]),
             tx(-22, -15, '−' if top == '-' else '+', 'pin', ctr=True), tx(-22, 15, '+' if top == '-' else '−', 'pin', ctr=True),
             pl([(-30, -15), (-36, -15)]), pl([(-30, 15), (-36, 15)]), pl([(32, 0), (36, 0)])]
    if p.get('comparator'):
        prims.append(pl([(-6, 5), (0, 5), (0, -5), (6, -5)], 'w thin'))
    pins = {'inm': (-36, -15 if top == '-' else 15), 'inp': (-36, 15 if top == '-' else -15), 'out': (36, 0)}
    if p['supply']:
        prims += [pl([(0, -17), (0, -30)]), pl([(0, 17), (0, 30)])]
        pins.update({'vp': (0, -30), 'vn': (0, 30)})
    return G(prims, pins, above(-36) if not p['supply'] else right(22, -22))


@symbol('fdamp', 'Fully differential amp', 'Analog', 'U', None, {'vocm': FLAG(True, 'VOCM pin')},
        fields=('GBW', 'Supply range'))
def fdamp(p):
    prims = [pg([(-30, -32), (-30, 32), (32, 0)]),
             tx(-22, -15, '+', 'pin', ctr=True), tx(-22, 15, '−', 'pin', ctr=True),
             pl([(-30, -15), (-40, -15)]), pl([(-30, 15), (-40, 15)]),
             pl([(14, -10), (40, -10)]), pl([(14, 10), (40, 10)]),
             tx(4, -6, '−', 'valsm', ctr=True), tx(4, 6, '+', 'valsm', ctr=True)]
    pins = {'inp': (-40, -15), 'inm': (-40, 15), 'outm': (40, -10), 'outp': (40, 10)}
    if p['vocm']:
        prims.append(pl([(-10, 21), (-10, 30)])); pins['vocm'] = (-10, 30)
    return G(prims, pins, above(-36))


@symbol('inamp', 'Instrumentation amp', 'Analog', 'U', None, {'rg': FLAG(True, 'Gain pins (RG)'), 'ref': FLAG(True, 'REF pin')},
        fields=('Gain', 'CMRR', 'Supply range'), aliases=('INA128', 'AD620', 'INA333'))
def inamp(p):
    prims = [pg([(-30, -32), (-30, 32), (32, 0)]), tx(-22, -20, '−', 'pin', ctr=True), tx(-22, 20, '+', 'pin', ctr=True),
             pl([(-30, -20), (-40, -20)]), pl([(-30, 20), (-40, 20)]), pl([(32, 0), (40, 0)]),
             tx(-4, 0, 'IA', 'valsm', ctr=True)]
    pins = {'inm': (-40, -20), 'inp': (-40, 20), 'out': (40, 0)}
    if p['rg']:
        prims += [pl([(-30, -5), (-40, -5)]), pl([(-30, 5), (-40, 5)])]
        pins.update({'rg1': (-40, -5), 'rg2': (-40, 5)})
    if p.get('ref'):
        prims.append(pl([(0, 16), (0, 30)])); pins['ref'] = (0, 30)
    return G(prims, pins, above(-36))


@symbol('regulator', 'Voltage regulator', 'Analog', 'U', 'X {IN} {GND} {OUT} {model}',
        {'kind': ENUM('fixed', ['fixed', 'adjustable'], 'Kind'), 'enable': FLAG(False, 'Enable pin')},
        model='VREG', fields=('Output voltage', 'Dropout', 'Max current'),
        pin_numbers={'IN': '1', 'GND': '2', 'OUT': '3', 'ADJ': '2', 'EN': '4'},
        aliases=('LM7805_TO220', 'L7805', 'AMS1117-3.3', 'LM317_TO-220', 'LM1117-3.3', 'Regulator', 'LDO'))
def regulator(p):
    adj = p['kind'] == 'adjustable'
    prims = [rc(-30, -20, 60, 40, 'box', 3), pl([(-40, -5), (-30, -5)]), pl([(30, -5), (40, -5)]), pl([(0, 20), (0, 30)]),
             tx(-26, -5, 'IN', 'valsm', 'start', ctr=True), tx(26, -5, 'OUT', 'valsm', 'end', ctr=True),
             tx(0, 13, 'ADJ' if adj else 'GND', 'valsm', ctr=True)]
    pins = {'IN': (-40, -5), 'OUT': (40, -5), ('ADJ' if adj else 'GND'): (0, 30)}
    if p['enable']:
        prims += [pl([(-40, 10), (-30, 10)]), tx(-26, 10, 'EN', 'valsm', 'start', ctr=True)]
        pins['EN'] = (-40, 10)
    return G(prims, pins, above(-26))


@symbol('vref', 'Shunt reference (TL431)', 'Analog', 'U', None, {}, fields=('Reference voltage', 'Tolerance'),
        pin_numbers={'REF': '1', 'A': '2', 'K': '3'}, aliases=('TL431', 'TL431DBZ', 'LM4040', 'Vref'))
def vref(p):
    prims = [pl([(0, -30), (0, -7)]), pg([(-7, 7), (7, 7), (0, -6)]), pl([(-9, -9), (-7, -6), (7, -6), (9, -3)], 'w plate'),
             pl([(0, 7), (0, 30)]), pl([(-30, 0), (-3, 0)])]
    return G(prims, {'K': (0, -30), 'A': (0, 30), 'REF': (-30, 0)}, right(12))


@symbol('sensor', 'Sensor (generic)', 'Analog', 'U', None,
        {'quantity': Prop('T', 'str', True, label='Quantity', help='letter or short text inside, e.g. T, P, B, RH')},
        fields=('Range', 'Accuracy', 'Interface'))
def sensor(p):
    prims = [rc(-15, -15, 30, 30, 'box', 3), tx(0, 0, str(p['quantity']), 'ref', ctr=True, fit=26),
             pl([(-15, 0), (-25, 0)]), pl([(15, 0), (25, 0)]), pl([(-11, 15), (11, -15)], 'w thin')]
    return G(prims, {'1': (-25, 0), '2': (25, 0)}, above(-21))
