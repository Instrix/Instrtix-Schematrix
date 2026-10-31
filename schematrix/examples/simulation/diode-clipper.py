# Diode clipper: two antiparallel diodes limit a 5 V sine to about +-0.7 V.
from schematrix import Schematic

s = Schematic('Diode clipper', description='Antiparallel diodes clamp the output to one diode drop')
v1 = s.vsrc(anchor='p', at=(60, 90), rot=90, length=80, kind='ac', value='SIN(0 5 1k)', ref='V1')
s.gnd(v1['n'])
r1 = s.resistor(anchor='1', at=(60, 60), value='1 k\\ohm', ref='R1')
s.wire(v1['p'], r1['1'])
d1 = s.diode(anchor='A', at=(150, 60), rot=90, ref='D1')
d2 = s.diode(anchor='K', at=(230, 60), rot=270, ref='D2')
s.wire(r1['2'], (230, 60)); s.gnd(d1['K']); s.gnd(d2['A'])
s.flag(s.wire((230, 60), (270, 60))[-1], 'OUT', side='right')
s.directive('.tran 5u 3m', '.meas tran vmax MAX v(OUT)', '.meas tran vmin MIN v(OUT)')
s.show()
