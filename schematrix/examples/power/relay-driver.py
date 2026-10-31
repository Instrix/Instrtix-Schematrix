# Logic-level relay driver: NPN low-side switch, base resistor, flyback diode across the coil.
from schematrix import Schematic

s = Schematic('Relay driver', description='3.3 V logic switching a 12 V relay coil')
k1 = s.relay(anchor='A1', at=(200, 40), contact='spdt', ref='K1', part='G5LE-1', label_offset=(70, 0),
             fields={'Coil voltage': ('12 V', True)})
s.rail(s.wire(k1['A1'], (200, 20))[-1], '+12 V')
d1 = s.diode(anchor='K', at=(150, 40), rot=270, ref='D1', part='1N4148', label_offset=(-40, 0))
s.wire(d1['K'], k1['A1']); s.wire(d1['A'], k1['A2'])
q = s.npn(anchor='C', at=(200, 140), ref='Q1', part='BC817')
s.wire(k1['A2'], q['C'])
s.gnd(q['E'])
rb = s.resistor(anchor='2', at=q['B'], value='1 k\\ohm', ref='R1')
s.flag(s.wire(rb['1'], (rb['1'][0] - 20, rb['1'][1]))[-1], 'RELAY_{EN}', side='left')
s.flag(s.wire(k1['NC'], (k1['NC'][0], 5), (320, 5))[-1], 'LOAD_{NC}', side='right')
s.flag(s.wire(k1['NO'], (k1['NO'][0], 25), (320, 25))[-1], 'LOAD_{NO}', side='right')
s.flag(s.wire(k1['COM'], (k1['COM'][0], 160), (320, 160))[-1], 'LOAD_{COM}', side='right')
s.show()
