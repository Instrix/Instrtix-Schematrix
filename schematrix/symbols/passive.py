"""Passive components: resistors and their variants, capacitors, inductors, transformers, fuses, crystals."""
from __future__ import annotations

import math

from .core import (BODY, ENUM, FLAG, LEN, G, above, below, ci, half, iec_box, leads, light, pg, pl, preset,
                   symbol, two_pins, tx, variable, vcoil)

R_FIELDS = ('Tolerance', 'Power', 'Tempco', 'Voltage rating')
C_FIELDS = ('Voltage rating', 'Tolerance', 'Dielectric', 'ESR')
L_FIELDS = ('Current rating', 'Saturation current', 'DCR', 'Tolerance')


# ---------------------------------------------------------------- resistors
@symbol('resistor', 'Resistor', 'Passive', 'R', 'R {1} {2} {value}',
        {'length': LEN(60), 'body': BODY(36), 'shape': ENUM('zigzag', ['zigzag', 'iec'], 'Shape')},
        fields=R_FIELDS, aliases=('R', 'R_Small', 'R_US', 'Resistor'))
def resistor(p):
    L = abs(float(p['length'])); h = L / 2; body = min(float(p['body']), L); a = -body / 2
    if p['shape'] == 'iec':
        return G([*leads(h, body / 2), pl([(a, -6), (-a, -6), (-a, 6), (a, 6), (a, -6)])],
                 {'1': (-h, 0), '2': (h, 0)}, above(-12))
    pts = [(-h, 0), (a, 0)]
    for i in range(6):
        pts.append((a + body * (i + 0.5) / 6, -6 if i % 2 == 0 else 6))
    pts += [(a + body, 0), (h, 0)]
    return G([pl(pts)], {'1': (-h, 0), '2': (h, 0)}, above(-12))


def _r_body(p):
    """resistor geometry used as the base of the variants"""
    return resistor({'length': p.get('length', 60), 'body': p.get('body', 36), 'shape': p.get('shape', 'zigzag')})


R_VARIANT = {'length': LEN(60), 'body': BODY(36), 'shape': ENUM('zigzag', ['zigzag', 'iec'], 'Shape')}


@symbol('rvar', 'Variable resistor', 'Passive', 'R', 'R {1} {2} {value}', R_VARIANT, fields=R_FIELDS,
        aliases=('R_Variable',))
def rvar(p):
    g = _r_body(p)
    g['prims'] += variable(18)
    g['label'] = above(-17)
    return g


@symbol('potentiometer', 'Potentiometer', 'Passive', 'RV', None,
        {'length': LEN(60), 'body': BODY(36), 'kind': ENUM('pot', ['pot', 'trimmer'], 'Kind')},
        fields=R_FIELDS, aliases=('R_POT', 'R_Potentiometer', 'R_POT_TRIM'), pin_numbers={'1': '1', 'W': '2', '2': '3'})
def potentiometer(p):
    g = resistor({**p, 'shape': 'zigzag'})
    if p.get('kind') == 'trimmer':
        g['prims'] += [pl([(0, -24), (0, -9)]), pl([(-5, -9), (5, -9)])]
    else:
        g['prims'] += [pl([(0, -24), (0, -9)]), pg([(-3.5, -14), (3.5, -14), (0, -8)], 'arrow')]
    g['pins']['W'] = [0, -24]
    g['label'] = below(14)
    return g


@symbol('thermistor', 'Thermistor', 'Passive', 'TH', 'R {1} {2} {value}',
        {'length': LEN(60), 'kind': ENUM('ntc', ['ntc', 'ptc'], 'Kind')}, fields=('Beta', 'R25', 'Tolerance'),
        aliases=('Thermistor', 'Thermistor_NTC', 'Thermistor_PTC'))
def thermistor(p):
    h = half(p)
    prims = [*leads(h, 14), iec_box(14), pl([(-22, 12), (-16, 12), (16, -12)]),
             tx(-22, 22, '−t°' if p['kind'] == 'ntc' else '+t°', 'valsm', 'start', ctr=True)]
    return G(prims, two_pins(h), above(-17))


@symbol('varistor', 'Varistor (VDR)', 'Passive', 'RV', 'R {1} {2} {value}', {'length': LEN(60)},
        fields=('Clamping voltage', 'Energy'), aliases=('Varistor',))
def varistor(p):
    h = half(p)
    prims = [*leads(h, 14), iec_box(14), pl([(-22, 12), (-16, 12), (16, -12)]), tx(18, -14, 'U', 'valsm', 'start', ctr=True)]
    return G(prims, two_pins(h), above(-17))


@symbol('ldr', 'Photoresistor (LDR)', 'Passive', 'R', 'R {1} {2} {value}', R_VARIANT, aliases=('R_Photo', 'LDR'))
def ldr(p):
    g = _r_body(p)
    g['prims'] += light(-8, -12, inward=True)
    g['label'] = above(-24)
    return g


@symbol('shunt', 'Current shunt (Kelvin)', 'Passive', 'R', 'R {1} {2} {value}', {'length': LEN(60)},
        fields=R_FIELDS, aliases=('R_Shunt',), pin_numbers={'1': '1', 'S1': '2', 'S2': '3', '2': '4'})
def shunt(p):
    h = half(p)
    prims = [*leads(h, 16), iec_box(16), pl([(-10, -6), (-10, -20)]), pl([(10, -6), (10, -20)])]
    return G(prims, {'1': (-h, 0), '2': (h, 0), 'S1': (-10, -20), 'S2': (10, -20)}, below(12))


# ---------------------------------------------------------------- capacitors
@symbol('capacitor', 'Capacitor', 'Passive', 'C', 'C {1} {2} {value}',
        {'length': LEN(40), 'polarized': FLAG(False, 'Polarized'),
         'plate': ENUM('flat', ['flat', 'curved'], 'Negative plate', help='curved: electrolytic style')},
        fields=C_FIELDS, aliases=('C', 'C_Small', 'C_Polarized', 'CP', 'C_Polarized_Small', 'CP_Small'))
def capacitor(p):
    h = abs(float(p['length'])) / 2
    if p.get('plate') == 'curved':
        prims = [pl([(-h, 0), (-4, 0)]), pl([(-4, -11), (-4, 11)], 'w plate'),
                 pl([(9 - 5 * math.cos(math.radians(a)), 11 * math.sin(math.radians(a))) for a in range(-90, 91, 15)], 'w plate'),
                 pl([(4, 0), (h, 0)])]
    else:
        prims = [*leads(h, 4), pl([(-4, -11), (-4, 11)], 'w plate'), pl([(4, -11), (4, 11)], 'w plate')]
    if p['polarized']:
        prims.append(tx(-12, -12, '+', 'valsm', ctr=True))
    return G(prims, {'1': (-h, 0), '2': (h, 0)}, above(-16))


@symbol('cvar', 'Variable capacitor', 'Passive', 'C', 'C {1} {2} {value}',
        {'length': LEN(40), 'kind': ENUM('variable', ['variable', 'trimmer'], 'Kind')}, fields=C_FIELDS,
        aliases=('C_Variable', 'C_Trim'))
def cvar(p):
    h = half(p, 40)
    prims = [*leads(h, 4), pl([(-4, -11), (-4, 11)], 'w plate'), pl([(4, -11), (4, 11)], 'w plate')]
    prims += variable(13) if p['kind'] == 'variable' else preset(13)
    return G(prims, two_pins(h), above(-17))


# ---------------------------------------------------------------- inductors and magnetics
def _core(prims, x0, x1, y, kind):
    if kind == 'iron':
        prims += [pl([(x0, y), (x1, y)]), pl([(x0, y - 3), (x1, y - 3)])]
    elif kind == 'ferrite':
        prims += [pl([(x0, y), (x1, y)], 'w para'), pl([(x0, y - 3), (x1, y - 3)], 'w para')]


CORE = ENUM('air', ['air', 'iron', 'ferrite'], 'Core')


@symbol('inductor', 'Inductor', 'Passive', 'L', 'L {1} {2} {value}', {'length': LEN(60), 'body': BODY(40), 'core': CORE},
        fields=L_FIELDS, aliases=('L', 'L_Small', 'L_Core_Iron', 'L_Core_Ferrite', 'Inductor'))
def inductor(p):
    h = abs(float(p['length'])) / 2; body = min(float(p['body']), 2 * h); a = -body / 2; r = body / 8
    pts = [(-h, 0), (a, 0)]
    for k in range(4):
        cx = a + r + 2 * r * k
        for j in range(1, 11):
            t = math.pi - math.pi * j / 10
            pts.append((cx + r * math.cos(t), -r * math.sin(t)))
    pts.append((h, 0))
    prims = [pl(pts)]
    _core(prims, a, -a, -r - 4, p.get('core', 'air'))
    return G(prims, {'1': (-h, 0), '2': (h, 0)}, above(-12 if p.get('core', 'air') == 'air' else -r - 10))


@symbol('ferrite', 'Ferrite bead', 'Passive', 'FB', 'L {1} {2} {value}', {'length': LEN(40)},
        fields=('Impedance @100MHz', 'Current rating'), aliases=('Ferrite_Bead', 'FerriteBead', 'Ferrite_Bead_Small'))
def ferrite(p):
    h = half(p, 40)
    c, s = math.cos(math.radians(-60)), math.sin(math.radians(-60))
    rect = [(-4, -9), (4, -9), (4, 9), (-4, 9)]
    return G([*leads(h, 0), pg([(x * c - y * s, x * s + y * c) for x, y in rect], 'box')], two_pins(h), above(-14))


@symbol('transformer', 'Transformer', 'Passive', 'T', None,
        {'core': ENUM('iron', ['air', 'iron', 'ferrite'], 'Core'), 'ct': FLAG(False, 'Centre tap'),
         'dots': FLAG(True, 'Polarity dots')},
        fields=('Turns ratio', 'Power', 'Isolation'), aliases=('Transformer_1P_1S', 'Transformer', 'TR'),
        pin_numbers={'P1': '1', 'P2': '2', 'S1': '3', 'S2': '4', 'CT': '5'})
def transformer(p):
    prims = [pl([(-30, -30), (-12, -30), (-12, -20)]), pl(vcoil(-12, -20, 20, 4, right=True)),
             pl([(-12, 20), (-12, 30), (-30, 30)]),
             pl([(30, -30), (12, -30), (12, -20)]), pl(vcoil(12, -20, 20, 4, right=False)),
             pl([(12, 20), (12, 30), (30, 30)])]
    pins = {'P1': (-30, -30), 'P2': (-30, 30), 'S1': (30, -30), 'S2': (30, 30)}
    k = p['core']
    if k != 'air':
        cl = 'w' if k == 'iron' else 'w para'
        prims += [pl([(-2, -22), (-2, 22)], cl), pl([(2, -22), (2, 22)], cl)]
    if p['ct']:
        prims.append(pl([(12, 0), (30, 0)])); pins['CT'] = (30, 0)
    if p['dots']:
        prims += [ci(-18, -22, 2), ci(18, -22, 2)]
    return G(prims, pins, above(-36))


@symbol('fuse', 'Fuse', 'Passive', 'F', 'R {1} {2} 10m', {'length': LEN(60)},
        fields=('Current rating', 'Voltage rating', 'Speed'), aliases=('Fuse', 'Fuse_Small', 'Polyfuse'))
def fuse(p):
    h = abs(float(p['length'])) / 2
    return G([*leads(h, 12), pl([(-12, -5), (12, -5), (12, 5), (-12, 5), (-12, -5)]), pl([(-12, 0), (12, 0)], 'w thin')],
             {'1': (-h, 0), '2': (h, 0)}, above(-11))


@symbol('crystal', 'Crystal', 'Passive', 'Y', None, {'length': LEN(60)},
        fields=('Load capacitance', 'Tolerance', 'ESR'), aliases=('Crystal', 'Crystal_Small', 'Resonator'))
def crystal(p):
    h = abs(float(p['length'])) / 2
    return G([*leads(h, 10), pl([(-10, -10), (-10, 10)], 'w plate'), pl([(10, -10), (10, 10)], 'w plate'),
              pl([(-5, -12), (5, -12), (5, 12), (-5, 12), (-5, -12)])],
             {'1': (-h, 0), '2': (h, 0)}, above(-17))


@symbol('spark_gap', 'Spark gap / GDT', 'Passive', 'E', None, {'length': LEN(60)},
        fields=('Spark-over voltage',), aliases=('Gas_Discharge_Tube', 'Spark_Gap', 'GDT'))
def spark_gap(p):
    h = half(p)
    prims = [pl([(-h, 0), (-10, 0)]), pg([(-10, 0), (-3, -4), (-3, 4)], 'arrow'),
             pl([(10, 0), (h, 0)]), pg([(10, 0), (3, -4), (3, 4)], 'arrow'), ci(0, 0, 13, 'w')]
    return G(prims, two_pins(h), above(-18))

