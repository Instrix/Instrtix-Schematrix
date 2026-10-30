"""Semiconductors: diodes of every kind, rectifier bridges, thyristors, BJTs, MOSFETs, JFETs, IGBTs, optocouplers."""
from __future__ import annotations

import math

from .core import ENUM, FLAG, LEN, G, above, arrow, ci, head, light, pg, pl, rc, right, symbol, tx

D_FIELDS = ('Reverse voltage', 'Forward current', 'Forward voltage', 'Power')
Q_FIELDS = ('Vce max', 'Ic max', 'hFE', 'Power')
M_FIELDS = ('Vds max', 'Id max', 'Rds(on)', 'Vgs(th)')

DIODE_KINDS = ['standard', 'schottky', 'zener', 'avalanche', 'tvs', 'tvs_uni', 'led', 'photodiode', 'varactor', 'tunnel',
               'pin', 'laser', 'step_recovery', 'shockley']

DIODE_PRESETS = (
    ('zener', 'Zener diode', {'kind': 'zener'}, ('D_Zener', 'D_Zener_Small', 'BZX84', 'Zener')),
    ('schottky', 'Schottky diode', {'kind': 'schottky'}, ('D_Schottky', 'D_Schottky_Small', 'BAT54', 'Schottky')),
    ('led', 'LED', {'kind': 'led'}, ('LED', 'LED_Small', 'LED_Filled')),
    ('tvs_diode', 'TVS diode', {'kind': 'tvs_uni'}, ('D_TVS_Unidirectional', 'TVS')),
    ('tvs_bidirectional', 'TVS diode, bidirectional', {'kind': 'tvs'}, ('D_TVS', 'D_TVS_Small', 'SMBJ', 'TVS_Bi')),
    ('avalanche_diode', 'Avalanche diode', {'kind': 'avalanche'}, ('D_Avalanche',)),
    ('photodiode', 'Photodiode', {'kind': 'photodiode'}, ('D_Photo', 'Photodiode', 'BPW34')),
    ('varactor', 'Varactor (varicap)', {'kind': 'varactor'}, ('D_Capacitance', 'D_Varactor', 'Varicap')),
    ('tunnel_diode', 'Tunnel diode', {'kind': 'tunnel'}, ('D_Tunnel',)),
    ('pin_diode', 'PIN diode', {'kind': 'pin'}, ('D_PIN', 'PIN_Diode')),
    ('laser_diode', 'Laser diode', {'kind': 'laser'}, ('LASER_Diode', 'Laser_Diode')),
    ('step_recovery_diode', 'Step-recovery diode', {'kind': 'step_recovery'}, ('D_SRD',)),
    ('shockley_diode', 'Shockley (4-layer) diode', {'kind': 'shockley'}, ('D_Shockley',)),
)


# ---------------------------------------------------------------- diodes
@symbol('diode', 'Diode', 'Semiconductor', 'D', 'D {A} {K} {model}',
        {'length': LEN(60), 'kind': ENUM('standard', DIODE_KINDS, 'Kind')}, model='DMOD', fields=D_FIELDS,
        pin_numbers={'K': '1', 'A': '2'}, presets=DIODE_PRESETS,
        aliases=('D', 'D_Small', 'D_Filled', 'Diode', '1N4148', '1N4007'))
def diode(p):
    h = abs(float(p['length'])) / 2
    k = p['kind']
    if k == 'tvs':                      # bidirectional: two triangles meeting at a zener bar
        prims = [pl([(-h, 0), (-13, 0)]), pg([(-13, -7), (-13, 7), (0, 0)]), pg([(13, -7), (13, 7), (0, 0)]),
                 pl([(13, 0), (h, 0)]), pl([(-4, -9), (0, -7), (0, 7), (4, 9)], 'w plate')]
        return G(prims, {'A': (-h, 0), 'K': (h, 0)}, above(-12))
    prims = [pl([(-h, 0), (-7, 0)]), pg([(-7, -7), (-7, 7), (6, 0)]), pl([(6, 0), (h, 0)])]
    lab = -12
    if k == 'schottky':
        prims.append(pl([(10, -4), (10, -7), (6, -7), (6, 7), (2, 7), (2, 4)], 'w plate'))
    elif k == 'zener':
        prims.append(pl([(2, -9), (6, -7), (6, 7), (10, 9)], 'w plate'))
    elif k == 'tvs_uni':                # unidirectional TVS: a zener bar with both ends bent back
        prims.append(pl([(2, -9), (6, -7), (6, 7), (2, 9)], 'w plate'))
    elif k == 'avalanche':              # bar with both ends bent towards the cathode
        prims.append(pl([(10, -9), (6, -7), (6, 7), (10, 9)], 'w plate'))
    elif k == 'tunnel':
        prims.append(pl([(2, -7), (6, -7), (6, 7), (2, 7)], 'w plate'))
    elif k == 'varactor':
        prims += [pl([(6, -7), (6, 7)], 'w plate'), pl([(11, -7), (11, 7)], 'w plate')]
        prims[2] = pl([(11, 0), (h, 0)])
    elif k == 'pin':                    # the intrinsic layer drawn as a box between anode and cathode
        prims[1] = pg([(-9, -7), (-9, 7), (3, 0)])
        prims += [pl([(3, -7), (3, 7)], 'w plate'), pl([(3, -7), (9, -7), (9, 7), (3, 7)], 'w thin'),
                  pl([(9, -7), (9, 7)], 'w plate')]
        prims[2] = pl([(9, 0), (h, 0)])
    elif k == 'step_recovery':          # bar with a short tail on each end, pointing back
        prims.append(pl([(6, -7), (6, 7)], 'w plate'))
        prims += [pl([(6, -7), (3, -10)]), pl([(6, 7), (9, 10)])]
    elif k == 'shockley':               # four-layer diode: the bar is bent into a step
        prims.append(pl([(6, -7), (6, 7), (1, 7)], 'w plate'))
    else:
        prims.append(pl([(6, -7), (6, 7)], 'w plate'))
    if k in ('led', 'laser'):
        for dx in (-4, 3):
            prims += [pl([(dx, -10), (dx + 6, -17)]), pg([(dx + 8, -19.5), (dx + 3.2, -17.5), (dx + 6.6, -14.4)], 'arrow')]
        if k == 'laser':
            prims.append(pl([(-7, -11), (6, -11)], 'w thin'))
        lab = -22
    elif k == 'photodiode':
        prims += light(-4, -11, inward=True)
        lab = -24
    return G(prims, {'A': (-h, 0), 'K': (h, 0)}, above(lab))


def _small_diode(a, b, s=5):
    """a small diode drawn on the segment a -> b (conducting a to b), centred on it"""
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    n = math.hypot(b[0] - a[0], b[1] - a[1]); ux, uy = (b[0] - a[0]) / n, (b[1] - a[1]) / n
    base = (mx - ux * s * 0.6, my - uy * s * 0.6); tip = (mx + ux * s * 0.6, my + uy * s * 0.6)
    return [pg([(base[0] - uy * s, base[1] + ux * s), (base[0] + uy * s, base[1] - ux * s), tip], 'arrow'),
            pl([(tip[0] - uy * s, tip[1] + ux * s), (tip[0] + uy * s, tip[1] - ux * s)], 'w plate')]


@symbol('bridge', 'Bridge rectifier', 'Semiconductor', 'D', None, {}, fields=D_FIELDS,
        aliases=('D_Bridge_+-AA', 'D_Bridge_+AA-', 'Bridge_Rectifier'),
        pin_numbers={'+': '1', 'AC1': '2', 'AC2': '3', '-': '4'})
def bridge(p):
    L, T, R, B = (-25, 0), (0, -25), (25, 0), (0, 25)
    prims = [pl([L, T, R, B, L], 'w thin')]
    for a, b in ((L, T), (R, T), (B, L), (B, R)):
        prims += _small_diode(a, b)
    prims += [pl([(-40, 0), L]), pl([R, (40, 0)]), pl([(0, -40), T]), pl([B, (0, 40)]),
              tx(7, -33, '+', 'valsm', 'start', ctr=True), tx(7, 33, '−', 'valsm', 'start', ctr=True)]
    return G(prims, {'AC1': (-40, 0), 'AC2': (40, 0), '+': (0, -40), '-': (0, 40)}, right(24, -22))


@symbol('scr', 'Thyristor (SCR)', 'Semiconductor', 'D', None, {'length': LEN(60)}, fields=D_FIELDS,
        aliases=('SCR', 'Thyristor'), pin_numbers={'K': '1', 'A': '2', 'G': '3'})
def scr(p):
    h = abs(float(p['length'])) / 2
    prims = [pl([(-h, 0), (-7, 0)]), pg([(-7, -7), (-7, 7), (6, 0)]), pl([(6, 0), (h, 0)]),
             pl([(6, -7), (6, 7)], 'w plate'), pl([(6, 5), (15, 14), (15, 20)])]
    return G(prims, {'A': (-h, 0), 'K': (h, 0), 'G': (15, 20)}, above(-12))


def _triac(p, gate):
    h = abs(float(p['length'])) / 2
    prims = [pl([(-h, 0), (-6, 0)]), pl([(6, 0), (h, 0)]), pl([(-6, -10), (-6, 10)], 'w plate'),
             pl([(6, -10), (6, 10)], 'w plate'), pg([(-6, -9), (-6, -1), (6, -5)]), pg([(6, 1), (6, 9), (-6, 5)])]
    pins = {'MT1': (-h, 0), 'MT2': (h, 0)}
    if gate:
        prims.append(pl([(6, 8), (15, 15), (15, 20)])); pins['G'] = (15, 20)
    return G(prims, pins, above(-14))


@symbol('triac', 'Triac', 'Semiconductor', 'Q', None, {'length': LEN(60)}, aliases=('Triac', 'TRIAC'),
        pin_numbers={'MT1': '1', 'MT2': '2', 'G': '3'})
def triac(p):
    return _triac(p, True)


@symbol('diac', 'Diac', 'Semiconductor', 'D', None, {'length': LEN(60)}, aliases=('Diac', 'DIAC'))
def diac(p):
    return _triac(p, False)


# ---------------------------------------------------------------- bipolar transistors
def _bjt(p, pnp):
    prims = [pl([(-30, 0), (-10, 0)]), pl([(-10, -14), (-10, 14)], 'w plate'),
             pl([(-10, -6), (0, -16), (0, -30)]), pl([(-10, 6), (0, 16), (0, 30)])]
    if pnp:
        prims.append(pg([(-8.5, 7.5), (-6.2, 13.6), (-2.4, 9.8)], 'arrow'))
    else:
        prims.append(pg([(-1.5, 14.5), (-8.4, 12.2), (-3.8, 7.6)], 'arrow'))
    if p.get('envelope'):
        prims.insert(0, ci(-6, 0, 21, 'w'))
    if p.get('photo'):
        prims += light(-24, -12, inward=True)
    return G(prims, {'C': (0, -30), 'B': (-30, 0), 'E': (0, 30)}, right(18 if p.get('envelope') else 8))


BJTPROPS = {'envelope': FLAG(False, 'Circle'), 'photo': FLAG(False, 'Phototransistor')}


@symbol('npn', 'NPN transistor', 'Semiconductor', 'Q', 'Q {C} {B} {E} {model}', BJTPROPS, model='NPN', fields=Q_FIELDS,
        pin_numbers={'B': '1', 'C': '2', 'E': '3'}, aliases=('Q_NPN_BCE', 'Q_NPN_CBE', 'Q_NPN_EBC', 'Q_NPN_BEC', 'Q_NPN',
                                                             'Q_Photo_NPN', 'NPN'))
def npn(p):
    return _bjt(p, False)


@symbol('pnp', 'PNP transistor', 'Semiconductor', 'Q', 'Q {C} {B} {E} {model}', BJTPROPS, model='PNP', fields=Q_FIELDS,
        pin_numbers={'B': '1', 'C': '2', 'E': '3'}, aliases=('Q_PNP_BCE', 'Q_PNP_CBE', 'Q_PNP_EBC', 'Q_PNP_BEC', 'Q_PNP', 'PNP'))
def pnp(p):
    return _bjt(p, True)


@symbol('darlington', 'Darlington (NPN)', 'Semiconductor', 'Q', None, {}, fields=Q_FIELDS,
        pin_numbers={'B': '1', 'C': '2', 'E': '3'}, aliases=('Q_NPN_Darlington_BCE', 'Q_NPN_Darlington'))
def darlington(p):
    prims = [pl([(-40, 10), (-25, 10)]), pl([(-25, 0), (-25, 20)], 'w plate'),
             pl([(-25, 5), (-17, -3), (-17, -20), (0, -20)]), pl([(-25, 15), (-12, 25), (-10, 25)]),
             pg([(-12, 25.5), (-19, 23.5), (-15, 19)], 'arrow'),
             pl([(-10, 15), (-10, 35)], 'w plate'), pl([(-10, 20), (0, 10), (0, -20)]),
             pl([(-10, 30), (0, 40), (0, 50)]), pg([(-1.5, 39), (-8, 36), (-4, 32.5)], 'arrow'), pl([(0, -20), (0, -30)])]
    return G(prims, {'C': (0, -30), 'B': (-40, 10), 'E': (0, 50)}, right(8, 10))


# ---------------------------------------------------------------- field-effect transistors
def _mos(p, pchan):
    dep = p.get('mode') == 'depletion'
    channel = [pl([(-9, -21), (-9, 21)], 'w plate')] if dep else \
        [pl([(-9, -21), (-9, -9)], 'w plate'), pl([(-9, -5), (-9, 5)], 'w plate'), pl([(-9, 9), (-9, 21)], 'w plate')]
    bulk = p.get('bulk')
    prims = [pl([(0, -30), (0, -15), (-9, -15)]), pl([(0, 30), (0, 15), (-9, 15)]),
             pl([(-9, 0), (20, 0)]) if bulk else pl([(-9, 0), (0, 0), (0, 15)]),
             *channel, pl([(-16, -17), (-16, 17)], 'w plate'), pl([(-30, 0), (-16, 0)]),
             pg([(-2, 0), (-8, -3.5), (-8, 3.5)] if pchan else [(-9, 0), (-3, -3.5), (-3, 3.5)], 'arrow')]
    if p.get('body_diode') and not bulk:
        prims += [pl([(0, -22), (10, -22), (10, 22), (0, 22)], 'w thin'),
                  pg([(5.5, 4), (14.5, 4), (10, -3)] if not pchan else [(5.5, -4), (14.5, -4), (10, 3)], 'amp'),
                  pl([(5.5, -3), (14.5, -3)] if not pchan else [(5.5, 4), (14.5, 4)], 'w')]
    pins = {'D': (0, -30), 'G': (-30, 0), 'S': (0, 30)}
    if bulk:
        pins['B'] = (20, 0)
    return G(prims, pins, right(22 if bulk else 16 if p.get('body_diode') else 8, -14 if bulk else 0))


MOSPROPS = {'body_diode': FLAG(False, 'Body diode'), 'mode': ENUM('enhancement', ['enhancement', 'depletion'], 'Mode'),
            'bulk': FLAG(False, 'Bulk pin', help='4-terminal: separate body connection')}


@symbol('nmos', 'N-MOSFET', 'Semiconductor', 'Q', 'M {D} {G} {S} {B|S} {model}', MOSPROPS, model='NMOS', fields=M_FIELDS,
        pin_numbers={'G': '1', 'D': '2', 'S': '3', 'B': '4'},
        aliases=('Q_NMOS_GDS', 'Q_NMOS_GSD', 'Q_NMOS_DGS', 'Q_NMOS_SGD', 'Q_NMOS', 'NMOS', 'Q_NMOS_Depletion'))
def nmos(p):
    return _mos(p, False)


@symbol('pmos', 'P-MOSFET', 'Semiconductor', 'Q', 'M {D} {G} {S} {B|S} {model}', MOSPROPS, model='PMOS', fields=M_FIELDS,
        pin_numbers={'G': '1', 'D': '2', 'S': '3', 'B': '4'},
        aliases=('Q_PMOS_GDS', 'Q_PMOS_GSD', 'Q_PMOS_DGS', 'Q_PMOS_SGD', 'Q_PMOS', 'PMOS'))
def pmos(p):
    return _mos(p, True)


def _jfet(p, pchan):
    prims = [pl([(0, -30), (0, -10), (-9, -10)]), pl([(0, 30), (0, 10), (-9, 10)]),
             pl([(-9, -16), (-9, 16)], 'w plate'), pl([(-30, 10), (-9, 10)])]
    prims.append(head((-17, 10), (-9, 10)) if pchan else head((-9, 10), (-17, 10)))
    return G(prims, {'D': (0, -30), 'G': (-30, 10), 'S': (0, 30)}, right(8))


@symbol('njfet', 'N-JFET', 'Semiconductor', 'Q', 'J {D} {G} {S} {model}', {}, model='NJF',
        pin_numbers={'D': '1', 'S': '2', 'G': '3'}, aliases=('Q_NJFET_DSG', 'Q_NJFET_DGS', 'Q_NJFET_GDS', 'Q_NJFET', 'NJFET'))
def njfet(p):
    return _jfet(p, False)


@symbol('pjfet', 'P-JFET', 'Semiconductor', 'Q', 'J {D} {G} {S} {model}', {}, model='PJF',
        pin_numbers={'D': '1', 'S': '2', 'G': '3'}, aliases=('Q_PJFET_DSG', 'Q_PJFET_DGS', 'Q_PJFET_GDS', 'Q_PJFET', 'PJFET'))
def pjfet(p):
    return _jfet(p, True)


@symbol('igbt', 'IGBT', 'Semiconductor', 'Q', None, {'body_diode': FLAG(False, 'Freewheel diode')},
        fields=('Vce max', 'Ic max', 'Vce(sat)'), pin_numbers={'G': '1', 'C': '2', 'E': '3'}, aliases=('Q_NIGBT_GCE', 'IGBT'))
def igbt(p):
    prims = [pl([(-30, 0), (-16, 0)]), pl([(-16, -14), (-16, 14)], 'w plate'), pl([(-10, -16), (-10, 16)], 'w plate'),
             pl([(-10, -7), (0, -16), (0, -30)]), pl([(-10, 7), (0, 16), (0, 30)]),
             pg([(-1.5, 15), (-8.4, 12.7), (-3.8, 8.1)], 'arrow')]
    if p.get('body_diode'):
        prims += [pl([(0, -22), (12, -22), (12, 22), (0, 22)], 'w thin'), pg([(7.5, 4), (16.5, 4), (12, -3)], 'amp'),
                  pl([(7.5, -3), (16.5, -3)])]
    return G(prims, {'C': (0, -30), 'G': (-30, 0), 'E': (0, 30)}, right(22 if p.get('body_diode') else 8))


@symbol('optocoupler', 'Optocoupler', 'Semiconductor', 'U', None, {'output': ENUM('transistor', ['transistor', 'triac'], 'Output')},
        fields=('CTR', 'Isolation'), pin_numbers={'A': '1', 'K': '2', 'E': '3', 'C': '4'},
        aliases=('PC817', 'Optocoupler', 'EL817', '4N35'))
def optocoupler(p):
    prims = [rc(-30, -30, 60, 60, 'w thin', 2),
             pl([(-40, -20), (-15, -20), (-15, -6)]), pl([(-40, 20), (-15, 20), (-15, 6)]),
             pg([(-22, -6), (-8, -6), (-15, 6)]), pl([(-22, 6), (-8, 6)], 'w plate'),
             *arrow((-5, -4), (5, -4), 4.5, 2.8), *arrow((-5, 4), (5, 4), 4.5, 2.8)]
    if p.get('output') == 'triac':
        prims += [pl([(40, -20), (18, -20), (18, -10)]), pl([(40, 20), (18, 20), (18, 10)]),
                  pl([(12, -10), (24, -10)], 'w plate'), pl([(12, 10), (24, 10)], 'w plate'),
                  pg([(13, -10), (19, -10), (16, 10)]), pg([(17, 10), (23, 10), (20, -10)])]
    else:
        prims += [pl([(12, -12), (12, 12)], 'w plate'), pl([(12, -5), (22, -14), (22, -20), (40, -20)]),
                  pl([(12, 5), (22, 14), (22, 20), (40, 20)]), pg([(22, 14.5), (15.4, 12.6), (19.4, 8.6)], 'arrow')]
    return G(prims, {'A': (-40, -20), 'K': (-40, 20), 'C': (40, -20), 'E': (40, 20)}, above(-36))
