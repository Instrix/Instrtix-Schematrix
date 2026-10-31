# An 8-bit accumulator datapath drawn with buses: adder -> register -> back into the adder.
from schematrix import Schematic

s = Schematic('8-bit accumulator', description='Bus-level datapath: ACC <= ACC + IN on every clock')
add = s.adder((160, 60), bits=8, bus=True, carry_in=False, ref='U1', part='74HC283 x2')
reg = s.register8((380, 60), bits=8, bus=True, oe=False, clear=True, ref='U2', part='74HC273')
s.wire(add['S'], (330, add['S'][1]), (330, reg['D'][1]), reg['D'], style='bus')
q = reg['Q']
s.wire(q, (q[0] + 30, q[1]), (q[0] + 30, 10), (130, 10), (130, add['A'][1]), add['A'], style='bus')
s.flag(s.wire((q[0] + 30, q[1]), (q[0] + 60, q[1]), style='bus')[-1], 'ACC[7:0]', side='right')
s.flag(s.wire(add['B'], (100, add['B'][1]), style='bus')[-1], 'IN[7:0]', side='left')
s.flag(s.wire(reg['CLK'], (340, reg['CLK'][1]))[-1], 'CLK', side='left')
s.flag(s.wire(reg['CLR'], (340, reg['CLR'][1]))[-1], '~{RST}', side='left')
co = add['CO']
s.flag(s.wire(co, (co[0] + 15, co[1]), (co[0] + 15, co[1] + 50), (co[0] + 35, co[1] + 50))[-1], 'C_{out}', side='right')
s.show()
