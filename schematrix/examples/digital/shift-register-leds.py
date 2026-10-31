# Serial-in / parallel-out shift register lighting eight LEDs. The outputs reach the LED bank by net labels,
# which keeps the drawing free of crossing wires.
from schematrix import Schematic

s = Schematic('Shift register and LEDs', description='74HC595-style SIPO register with eight LED outputs')
sr = s.shiftreg_sipo((120, 40), bits=8, oe=True, ref='U1', part='74HC595')
for name, lbl in (('SER', 'DATA'), ('CLK', 'CLK'), ('CLR', '~{CLR}'), ('OE', '~{OE}')):
    p = sr[name]
    s.flag(s.wire(p, (p[0] - 25, p[1]))[-1], lbl, side='left')
for i in range(8):
    q = sr[f'Q{i}']
    s.flag(s.wire(q, (q[0] + 25, q[1]))[-1], f'Q{i}', side='right')
x0, y0 = 360, 60
for i in range(8):
    x = x0 + 50 * i
    s.flag((x, y0), f'Q{i}', side='right', rot=0)
    r = s.resistor(anchor='1', at=(x, y0), rot=90, length=50, body=24, value='330', ref=f'R{i + 1}', hide_labels=True)
    d = s.led(anchor='A', at=r['2'], rot=90, ref=f'D{i + 1}', length=40, hide_labels=True)
    s.gnd(d['K'])
s.note(x0, y0 + 150, 'LED bank: R1..R8 = 330 \\ohm, D1..D8 red LEDs')
s.show()
