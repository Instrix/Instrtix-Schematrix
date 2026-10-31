# Buses: the register's Q output runs on a bus labelled Q[7:0]. Bus entries tap single bits off it; each tap
# carries the bit's name (Q0, Q1, ...) and drives an LED. The netlist connects U1.Q0 .. Q3 to the LEDs bit by bit.
from schematrix import Schematic

s = Schematic('Bus breakout', description='Bus labels, bus entries and bit-by-bit connectivity')
reg = s.register8((100, 40), bus=True, oe=False, ref='U1', part='74HC574')
s.flag(s.wire(reg['D'], (reg['D'][0] - 40, reg['D'][1]), style='bus')[-1], 'DATA[7:0]', side='left')
s.flag(s.wire(reg['CLK'], (reg['CLK'][0] - 40, reg['CLK'][1]))[-1], 'CLK', side='left')
q = reg['Q']
end = (q[0] + 300, q[1])
s.wire(q, end, style='bus')
s.flag(end, 'Q[7:0]', side='right')
for bit in range(4):
    x = q[0] + 60 + 60 * bit
    e = s.busentry((x, q[1]), direction='down')
    bx, by = e['bit']
    s.wire((bx, by), (bx, by + 40))
    s.flag((bx, by + 20), f'Q{bit}', side='right')           # the label names the tapped bit
    r = s.resistor(anchor='1', at=(bx, by + 40), rot=90, length=40, body=24, value='330', ref=f'R{bit + 1}', hide_labels=True)
    d = s.led(anchor='A', at=r['2'], rot=90, ref=f'D{bit + 1}', length=40, hide_labels=True)
    s.gnd(d['K'])
s.note(40, 250, 'A label like Q[7:0] names a bus; a wire labelled Q3 is bit 3 of it. R1..R4 = 330 \\ohm.')
s.show()
