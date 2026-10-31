# An 8-bit accumulator datapath drawn with buses: the adder's sum is clocked into the register, and the register
# feeds back into the adder:   ACC <= ACC + IN   on every clock.
from schematrix import Schematic

s = Schematic('8-bit accumulator', description='Bus-level datapath', hops=True)
add = s.adder((180, 60), bits=8, bus=True, carry_in=False, ref='U1', part='2 x 74HC283')
reg = s.register8((440, 40), bits=8, bus=True, oe=False, clear=True, ref='U2', part='74HC273')
reg.move(0, add['S'][1] - reg['D'][1])                         # line the sum up with the register input
s.wire(add['S'], reg['D'], style='bus')
q, a = reg['Q'], add['A']
low = max(add.bbox[3], reg.bbox[3]) + 30
s.wire(q, (q[0] + 30, q[1]), (q[0] + 30, low), (a[0] - 30, low), (a[0] - 30, a[1]), a, style='bus')
s.flag(s.wire((q[0] + 30, q[1]), (q[0] + 80, q[1]), style='bus')[-1], 'ACC[7:0]', side='right')
s.flag(s.wire(add['B'], (add['B'][0] - 60, add['B'][1]), style='bus')[-1], 'IN[7:0]', side='left')
s.flag(s.wire(reg['CLK'], (reg['CLK'][0] - 40, reg['CLK'][1]))[-1], 'CLK', side='left')
s.flag(s.wire(reg['CLR'], (reg['CLR'][0] - 40, reg['CLR'][1]))[-1], '~{RST}', side='left')
co = add['CO']
s.flag(s.wire(co, (co[0] + 20, co[1]), (co[0] + 20, low - 20), (co[0] + 40, low - 20))[-1], 'C_{out}', side='right')
s.show()
