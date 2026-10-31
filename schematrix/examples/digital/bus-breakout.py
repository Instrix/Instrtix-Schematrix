# Buses: a register's Q output runs on a bus labelled Q[7:0]; bus entries tap single bits off it, and each
# tapped wire joins its bit by name (Q0, Q1, ...). The netlist connects U1.Q3 to D4 bit by bit.
from schematrix import Schematic

s = Schematic('Bus breakout', description='Bus labels, bus entries and bit-by-bit connectivity')
reg = s.register8((100, 60), bus=True, oe=False, ref='U1', part='74HC574')
s.flag(s.wire(reg['D'], (reg['D'][0] - 40, reg['D'][1]), style='bus')[-1], 'DATA[7:0]', side='left')
s.flag(s.wire(reg['CLK'], (reg['CLK'][0] - 40, reg['CLK'][1]))[-1], 'CLK', side='left')
q = reg['Q']
end = (q[0] + 260, q[1])
s.wire(q, end, style='bus')
s.flag(end, 'Q[7:0]', side='right')
for k, bit in enumerate((0, 1, 2, 3)):
    x = q[0] + 50 + 50 * k
    e = s.busentry((x, q[1]), direction='down')
    tap = s.wire(e['bit'], (e['bit'][0], e['bit'][1] + 40))
    s.flag(tap[-1], f'Q{bit}', side='right')
    r = s.resistor(anchor='1', at=(x + 10, q[1] + 90), rot=90, length=40, body=24, value='330', ref=f'R{k + 1}', hide_labels=True)
    s.flag(r['1'], f'Q{bit}', side='left')
    d = s.led(anchor='A', at=r['2'], rot=90, ref=f'D{k + 1}', length=40, hide_labels=True)
    s.gnd(d['K'])
s.note(40, 300, 'Q[7:0] names the bus; a wire labelled Q3 (net label on the bus-entry tap) is bit 3 of it')
s.show()
