# Asynchronous buck converter, 12 V -> ~6 V at 50 % duty, 100 kHz. Simulate the start-up transient.
from schematrix import Schematic

s = Schematic('Buck converter', description='P-MOSFET high-side switch, Schottky catch diode, LC output filter')
q1 = s.pmos(anchor='S', at=(130, 40), rot=90, mirror=True, ref='Q1')   # source left, drain right, gate below
vin = s.vsrc(anchor='p', at=(60, 70), rot=90, length=80, value='12', ref='V1')
s.wire(vin['p'], (60, 40), q1['S'])
s.gnd(vin['n'])
vg = s.vsrc(anchor='p', at=(q1['G'][0], q1['G'][1] + 20), rot=90, length=80, kind='pulse', ref='V2',
            value='PULSE(0 12 0 20n 20n 5u 10u)')
s.wire(q1['G'], vg['p'])
s.gnd(vg['n'])
x = q1['D'][0] + 30
s.wire(q1['D'], (x, 40))
d1 = s.schottky(anchor='K', at=(x, 40), rot=270, ref='D1')
s.gnd(d1['A'])
l1 = s.inductor(anchor='1', at=(x, 40), value='47 \\uH', ref='L1')
c1 = s.capacitor(anchor='1', at=(l1['2'][0] + 40, 40), rot=90, value='100 \\uF', ref='C1')
s.wire(l1['2'], c1['1']); s.gnd(c1['2'])
rl = s.resistor(anchor='1', at=(c1['1'][0] + 70, 40), rot=90, value='5 \\ohm', ref='R_{L}')
s.wire(c1['1'], rl['1']); s.gnd(rl['2'])
s.flag(s.wire(rl['1'], (rl['1'][0] + 40, 40))[-1], 'V_{OUT}', side='right')
s.note(40, 230, 'V2 = 0 V turns Q1 on (V_{GS} = \\-12 V):  D = 50 %,  V_{OUT} \\approx D V_{in} \\approx 6 V')
s.directive('.tran 0.2u 3m uic')
s.show()
