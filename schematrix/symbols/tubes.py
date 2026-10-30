"""Vacuum tubes (valves): diode, triode, tetrode, pentode, with optional heater pins."""
from __future__ import annotations

from .core import FLAG, G, ci, pl, right, symbol

R = 30   # envelope radius


def _tube(p, grids):
    """grids: [(name, y, side)] drawn dashed between the plate (anode) and the cathode"""
    prims = [ci(0, 0, R, 'amp'),
             pl([(0, -45), (0, -16)]), pl([(-11, -16), (11, -16)], 'w plate'),           # plate
             pl([(-11, 13), (11, 13), (11, 17)]), pl([(11, 17), (15, 25), (15, 45)])]    # cathode
    pins = {'P': (0, -45), 'K': (15, 45)}
    for name, y, side in grids:
        prims.append(pl([(-12, y), (12, y)], 'w para'))
        x = -45 if side == 'l' else 45
        prims.append(pl([(x, y), (-12 if side == 'l' else 12, y)]))
        pins[name] = (x, y)
    if p.get('heater'):
        prims += [pl([(-15, 45), (-15, 24), (-10, 18), (-5, 24), (-5, 45)])]
        pins.update({'H1': (-15, 45), 'H2': (-5, 45)})
    return G(prims, pins, right(R + 6, -R + 4))


HEATER = {'heater': FLAG(False, 'Heater pins')}


@symbol('tube_diode', 'Vacuum diode', 'Vacuum tubes', 'V', None, HEATER, fields=('Heater voltage',), aliases=('EZ80', '5Y3'))
def tube_diode(p):
    return _tube(p, [])


@symbol('triode', 'Triode', 'Vacuum tubes', 'V', None, HEATER, fields=('Heater voltage', 'Mu'),
        aliases=('ECC83', '12AX7', 'ECC81', '12AT7', 'ECC82', '12AU7', 'Triode'))
def triode(p):
    return _tube(p, [('G', 0, 'l')])


@symbol('tetrode', 'Tetrode', 'Vacuum tubes', 'V', None, HEATER, fields=('Heater voltage',), aliases=('Tetrode', '6L6'))
def tetrode(p):
    return _tube(p, [('G1', 5, 'l'), ('G2', -5, 'r')])


@symbol('pentode', 'Pentode', 'Vacuum tubes', 'V', None, HEATER, fields=('Heater voltage',),
        aliases=('EL84', '6BQ5', 'EL34', 'EF86', 'Pentode'))
def pentode(p):
    return _tube(p, [('G1', 10, 'l'), ('G2', 0, 'r'), ('G3', -10, 'l')])
