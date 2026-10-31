# One-bit full adder from gates, drawn the textbook way: the inputs run down as vertical rails and every gate
# taps the rails it needs.   S = A xor B xor C_in,   C_out = A B + C_in (A xor B)
from schematrix import Schematic

s = Schematic('Full adder', description='Gate-level 1-bit full adder', hops=True)
RA, RB, RC = 80, 110, 140                      # rail x positions
x1 = s.xor_gate((240, 70), ref='U1')
a1 = s.and_gate((240, 170), ref='U2')
x2 = s.xor_gate((400, 90), ref='U3')
a2 = s.and_gate((400, 240), ref='U4')
o1 = s.or_gate((540, 205), ref='U5')
top, bottom = 30, 280
for x, name in ((RA, 'A'), (RB, 'B'), (RC, 'C_{in}')):
    s.flag(s.wire((x, bottom), (x, top))[-1], name, side='left' if x == RA else 'right', rot=0)
def tap(rail, pin):                            # rail -> gate input, straight across
    s.wire((rail, pin[1]), pin)
tap(RA, x1['in1']); tap(RB, x1['in2'])
tap(RA, a1['in1']); tap(RB, a1['in2'])
tap(RC, x2['in2']); tap(RC, a2['in2'])
xo = x1['out']
s.wire(xo, (310, xo[1]), (310, x2['in1'][1]), x2['in1'])
s.wire((310, x2['in1'][1]), (310, a2['in1'][1]), a2['in1'])
s.wire(a1['out'], (480, a1['out'][1]), (480, o1['in1'][1]), o1['in1'])
s.wire(a2['out'], (480 + 10, a2['out'][1]), (490, o1['in2'][1]), o1['in2'])
s.flag(s.wire(x2['out'], (620, x2['out'][1]))[-1], 'S', side='right')
s.flag(s.wire(o1['out'], (620, o1['out'][1]))[-1], 'C_{out}', side='right')
s.show()
