# A 3-bit counter driving a 3:8 decoder over a bus: one thick wire carries Q[2:0] to A[2:0].
from schematrix import Schematic

s = Schematic('Counter and decoder', description='Binary counter scanning eight active-low select lines')
ctr = s.counter((140, 60), bits=3, load=False, enable=False, carry=False, bus=True, ref='U1', part='74HC161')
dec = s.decoder((330, 40), bus=True, ref='U2', part='74HC138')
s.wire(ctr['Q'], (300, ctr['Q'][1]), (300, dec['A'][1]), dec['A'], style='bus')
s.gnd(s.wire(dec['E'], (310, dec['E'][1]), (310, dec['E'][1] + 20))[-1])
clk = s.vsrc(anchor='p', at=(70, ctr['CLK'][1] + 60), rot=90, length=80, kind='square', ref='V1',
             value='PULSE(0 5 0 1n 1n 50u 100u)')
s.wire(clk['p'], (70, ctr['CLK'][1]), ctr['CLK']); s.gnd(clk['n'])
s.rail(s.wire(ctr['CLR'], (110, ctr['CLR'][1]), (110, 30))[-1], '+5 V')
for i in range(8):                                   # labels alternate between two columns so they don't overlap
    p = dec[f'Y{i}']
    s.flag(s.wire(p, (p[0] + (20 if i % 2 == 0 else 80), p[1]))[-1], f'~{{SEL{i}}}', side='right')
s.show()
