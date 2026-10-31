# A 3-bit counter driving a 3:8 decoder over a bus: one thick wire carries Q[2:0] to A[2:0].
from schematrix import Schematic

s = Schematic('Counter and decoder', description='Binary counter scanning eight active-low select lines')
ctr = s.counter((160, 60), bits=3, load=False, enable=False, carry=False, bus=True, ref='U1', part='74HC161')
dec = s.decoder((360, 40), bus=True, ref='U2', part='74HC138')
s.wire(ctr['Q'], (320, ctr['Q'][1]), (320, dec['A'][1]), dec['A'], style='bus')
s.gnd(s.wire(dec['E'], (340, dec['E'][1]), (340, dec['E'][1] + 30))[-1])
s.flag(s.wire(ctr['CLK'], (ctr['CLK'][0] - 30, ctr['CLK'][1]))[-1], 'CLK', side='left')
s.flag(s.wire(ctr['CLR'], (ctr['CLR'][0] - 30, ctr['CLR'][1]))[-1], '~{RST}', side='left')
for i in range(8):
    p = dec[f'Y{i}']
    s.flag(s.wire(p, (p[0] + 20, p[1]))[-1], f'~{{SEL{i}}}', side='right')
clk = s.vsrc((80, 260), rot=90, length=80, kind='square', ref='V1', value='PULSE(0 5 0 1n 1n 50u 100u)')
s.flag(s.wire(clk['p'], (80, 200))[-1], 'CLK', side='right'); s.gnd(clk['n'])
s.show()
