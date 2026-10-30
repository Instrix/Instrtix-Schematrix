"""Electromechanical parts: switches and push buttons, relays, connectors, jumpers, antennas."""
from __future__ import annotations

from .core import ENUM, FLAG, LEN, G, Prop, above, below, ci, pl, rc, right, symbol, tx

SW_KINDS = ['spst', 'spdt', 'push_no', 'push_nc']


@symbol('switch', 'Switch / push button', 'Electromechanical', 'SW', None,
        {'length': LEN(60), 'kind': ENUM('spst', SW_KINDS, 'Kind'), 'closed': FLAG(False, 'Closed')},
        fields=('Current rating', 'Voltage rating'),
        aliases=('SW_SPST', 'SW_SPDT', 'SW_Push', 'SW_Push_Open', 'SW_Push_NC', 'SW_Push_Closed', 'Switch'))
def switch(p):
    h = abs(float(p['length'])) / 2
    k = p.get('kind', 'spst')
    if k == 'spdt':
        lever = [(-h + 18, -1), (h - 18, -8.5)] if p['closed'] else [(-h + 18, -1), (h - 18, 8.5)]
        return G([pl([(-h, 0), (-h + 14, 0)]), ci(-h + 16, 0, 2.5, 'pad'),
                  pl([(h, -10), (h - 14, -10)]), ci(h - 16, -10, 2.5, 'pad'),
                  pl([(h, 10), (h - 14, 10)]), ci(h - 16, 10, 2.5, 'pad'), pl(lever)],
                 {'1': (-h, 0), '2': (h, -10), '3': (h, 10)}, above(-18))
    if k in ('push_no', 'push_nc'):
        nc = k == 'push_nc'
        y = 4 if nc else -6
        prims = [pl([(-h, 0), (-h + 14, 0)]), pl([(h - 14, 0), (h, 0)]), ci(-h + 16, 0, 2.5, 'pad'), ci(h - 16, 0, 2.5, 'pad'),
                 pl([(-h + 14, y), (h - 14, y)]), pl([(0, y), (0, -16)]), pl([(-6, -16), (6, -16)])]
        return G(prims, {'1': (-h, 0), '2': (h, 0)}, above(-22))
    lever = [(-h + 18, -1), (h - 18, -3.5)] if p['closed'] else [(-h + 18, -1), (h - 16, -13)]
    return G([pl([(-h, 0), (-h + 14, 0)]), pl([(h - 14, 0), (h, 0)]), ci(-h + 16, 0, 2.5, 'pad'), ci(h - 16, 0, 2.5, 'pad'),
              pl(lever)], {'1': (-h, 0), '2': (h, 0)}, above(-18))


@symbol('relay', 'Relay', 'Electromechanical', 'K', None,
        {'contact': ENUM('spdt', ['spst', 'spdt'], 'Contact'), 'latching': FLAG(False, 'Latching')},
        fields=('Coil voltage', 'Coil resistance', 'Contact rating'),
        pin_numbers={'A1': '1', 'A2': '2', 'COM': '3', 'NO': '4', 'NC': '5'},
        aliases=('Relay_SPDT', 'Relay_SPST', 'Relay', 'G5LE-1', 'SRD-05VDC-SL-C'))
def relay(p):
    prims = [rc(-40, -12, 20, 24, 'box', 1), pl([(-30, -30), (-30, -12)]), pl([(-30, 12), (-30, 30)]),
             pl([(-40, -12), (-20, 12)], 'w thin'),
             pl([(15, 30), (15, 12)]), ci(15, 12, 2, 'dot'), pl([(15, 12), (4, -11)]),
             pl([(-20, 0), (9, 0)], 'w thin para'),
             pl([(30, -30), (30, -12), (24, -12)])]
    pins = {'A1': (-30, -30), 'A2': (-30, 30), 'COM': (15, 30), 'NO': (30, -30)}
    if p['contact'] == 'spdt':
        prims.append(pl([(0, -30), (0, -12), (5, -12)])); pins['NC'] = (0, -30)
    if p.get('latching'):
        prims.append(pl([(-40, 12), (-20, -12)], 'w thin'))
    return G(prims, pins, below(36))


@symbol('connector', 'Connector / header', 'Electromechanical', 'J', None,
        {'pins': Prop(4, 'num', True, label='Pins'), 'gender': ENUM('pin', ['pin', 'socket'], 'Style')},
        fields=('Pitch', 'Mating part'), aliases=('Conn_01x02', 'Conn_01x03', 'Conn_01x04', 'Conn_01x06', 'Conn_01x08',
                                                   'Conn_01x02_Pin', 'Conn_01x04_Pin', 'Conn_01x02_Socket', 'Screw_Terminal_01x02'))
def connector(p):
    n = max(1, min(40, int(float(p['pins']))))
    H = 10 * n + 10
    prims = [rc(-10, -5, 22, H, 'box', 1)]
    pins = {}
    for i in range(n):
        y = 10 * i + 5
        name = str(i + 1)
        prims += [pl([(-20, y), (-10, y)]), tx(-2, y, name, 'valsm', 'start', ctr=True)]
        prims.append(ci(-7, y, 1.6, 'dot') if p['gender'] == 'pin' else pl([(-10, y - 3), (-7, y), (-10, y + 3)], 'w thin'))
        pins[name] = (-20, y)
    return G(prims, pins, above(-10))


@symbol('jumper', 'Jumper / solder bridge', 'Electromechanical', 'JP', None,
        {'length': LEN(40), 'closed': FLAG(False, 'Closed')}, aliases=('Jumper', 'SolderJumper_2_Open', 'SolderJumper_2_Bridged'))
def jumper(p):
    h = abs(float(p['length'])) / 2
    prims = [pl([(-h, 0), (-6, 0)]), pl([(6, 0), (h, 0)]), ci(-6, 0, 2.5, 'pad'), ci(6, 0, 2.5, 'pad')]
    prims.append(pl([(-8, -6), (8, -6)]) if p['closed'] else pl([(-8, -6), (-8, -9), (8, -9), (8, -6)], 'w thin'))
    return G(prims, {'1': (-h, 0), '2': (h, 0)}, above(-14))


@symbol('antenna', 'Antenna', 'Electromechanical', 'AE', None, {'kind': ENUM('monopole', ['monopole', 'loop', 'dipole'], 'Kind')},
        fields=('Frequency', 'Gain', 'Impedance'), aliases=('Antenna', 'Antenna_Dipole', 'Antenna_Loop'))
def antenna(p):
    k = p['kind']
    if k == 'loop':
        prims = [pl([(-5, 0), (-5, -15), (-15, -15), (-15, -35), (15, -35), (15, -15), (5, -15), (5, 0)])]
        return G(prims, {'1': (-5, 0), '2': (5, 0)}, right(20, -25))
    if k == 'dipole':
        prims = [pl([(-5, 0), (-5, -20), (-25, -20)]), pl([(5, 0), (5, -20), (25, -20)])]
        return G(prims, {'1': (-5, 0), '2': (5, 0)}, above(-26))
    prims = [pl([(0, 0), (0, -30)]), pl([(-12, -42), (0, -30), (12, -42)]), pl([(0, -30), (0, -42)])]
    return G(prims, {'p': (0, 0)}, right(16, -34))

