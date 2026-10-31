# Series RLC band-pass: resonance at f0 = 1 / (2 pi sqrt(L C)) ~ 5.03 kHz, Q = (1/R) sqrt(L/C) = 10.
from schematrix import Schematic

s = Schematic('RLC resonance', description='AC sweep of a series RLC; .meas finds the peak and its frequency')
v1 = s.vsrc(anchor='p', at=(60, 90), rot=90, length=80, kind='ac', value='AC 1', ref='V1')
s.gnd(v1['n'])
l1 = s.inductor(anchor='1', at=(60, 60), value='10 mH', ref='L1')
s.wire(v1['p'], l1['1'])
c1 = s.capacitor(anchor='1', at=l1['2'], value='100 nF', ref='C1')
r1 = s.resistor(anchor='1', at=(c1['2'][0] + 20, 60), rot=90, value='31.6 \\ohm', ref='R1')
s.wire(c1['2'], r1['1']); s.gnd(r1['2'])
s.flag(s.wire(r1['1'], (r1['1'][0] + 40, 60))[-1], 'OUT', side='right')
s.directive('.ac dec 200 100 100k', '.meas ac peak MAX vm(OUT)', '.meas ac f0 WHEN vp(OUT)=0')
s.note(40, 200, 'f_{0} = 1 / (2\\pi \\sqrt{}LC) \\approx 5.03 kHz,   Q = 10')
s.show()
