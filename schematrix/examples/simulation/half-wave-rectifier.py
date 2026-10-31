# Half-wave rectifier with reservoir capacitor: watch the ripple. Uses the default diode model (DMOD).
from schematrix import Schematic

s = Schematic('Half-wave rectifier', description='10 V peak, 50 Hz, 1 kOhm load, 100 uF reservoir')
v1 = s.vsrc(anchor='p', at=(60, 90), rot=90, length=80, kind='ac', value='SIN(0 10 50)', ref='V1')
s.gnd(v1['n'])
d1 = s.diode(anchor='A', at=(60, 60), ref='D1')
s.wire(v1['p'], d1['A'])
c1 = s.electrolytic(anchor='1', at=(d1['K'][0] + 30, 60), rot=90, value='100 \\uF', ref='C1')
s.wire(d1['K'], c1['1']); s.gnd(c1['2'])
rl = s.resistor(anchor='1', at=(c1['1'][0] + 90, 60), rot=90, value='1 k\\ohm', ref='R_{L}')
s.wire(c1['1'], rl['1']); s.gnd(rl['2'])
s.flag(s.wire(rl['1'], (rl['1'][0] + 40, 60))[-1], 'OUT', side='right')
s.directive('.tran 50u 100m', '.meas tran vmax MAX v(OUT) FROM=60m TO=100m', '.meas tran vmin MIN v(OUT) FROM=60m TO=100m',
            '.meas tran ripple PARAM=\'vmax-vmin\'')
s.note(40, 200, 'Ripple \\le I / (f C) = 9.3 mA / (50 Hz \\times 100 \\uF) \\approx 1.9 V  (simulated: 1.5 V)')
s.show()
