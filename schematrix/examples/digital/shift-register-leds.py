# Serial-in / parallel-out shift register lighting eight LEDs; the outputs fan out over each other (wire hops on).
from schematrix import Schematic

s = Schematic('Shift register and LEDs', description='74HC595-style SIPO register with eight LED outputs', hops=True)
sr = s.shiftreg_sipo((120, 40), bits=8, oe=True, ref='U1', part='74HC595')
for name, lbl in (('SER', 'DATA'), ('CLK', 'CLK'), ('CLR', '~{CLR}'), ('OE', '~{OE}')):
    p = sr[name]
    s.flag(s.wire(p, (p[0] - 25, p[1]))[-1], lbl, side='left')
x0, top = sr['Q0'][0] + 40, sr['Q7'][1] + 30
for i in range(8):
    q = sr[f'Q{i}']
    x = x0 + 40 * i
    s.wire(q, (x, q[1]), (x, top))
    r = s.resistor(anchor='1', at=(x, top), rot=90, length=40, body=24, value='330', ref=f'R{i + 1}', hide_labels=True)
    d = s.led(anchor='A', at=r['2'], rot=90, ref=f'D{i + 1}', length=40, hide_labels=True)
    s.gnd(d['K'])
s.note(x0, top + 140, 'R1..R8 = 330 \\ohm,  D1..D8 red LEDs')
s.show()
