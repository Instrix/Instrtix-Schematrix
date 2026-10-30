# Build schematics in Python. Ctrl+Enter runs this; every schematic you
# create (or pass to show()) opens as a tab. Pins are reached as part['pin'].
from schematrix import Schematic

s = Schematic('RC filter and buffer', description='First-order low-pass into a follower')
vin = s.flag((60, 120), 'VIN', side='left')
r1 = s.resistor((130, 120), value='1 kΩ')
c1 = s.capacitor(anchor='1', at=(200, 120), rot=90, value='10 nF', part='C0G')
s.gnd(c1['2'])
u1 = s.opamp(anchor='inp', at=(280, 120), top='+', part='OPA210')
s.wire(vin['p'], r1['1'])
s.wire(r1['2'], u1['inp'])                     # passes over C1's pin: a junction dot appears

out = u1['out']
fb = s.wire(out, out.offset(20, 0), out.offset(20, 45), u1['inm'].offset(-14, 45 - 15), u1['inm'].offset(-14, 0), u1['inm'])
s.wire(out.offset(20, 0), out.offset(50, 0))
s.flag(out.offset(50, 0), 'VOUT', side='right')
s.note(60, 230, 'f_c = 1 / (2π · 1 kΩ · 10 nF) ≈ 15.9 kHz')

# a resistor ladder, drawn in a loop
lad = Schematic('Ladder')
top = lad.terminal((60, 40), 'I+')
prev = top['p']
for k, (r, tap) in enumerate([('10 mΩ', 't1'), ('90 mΩ', 't2'), ('900 mΩ', 't3')], 1):
    rk = lad.resistor(anchor='1', at=prev, rot=90, value=r, length=80, style='acc' if k == 3 else '')
    prev = rk['2']
    lad.wire(prev, prev.offset(60, 0))
    lad.flag(prev.offset(60, 0), tap.upper(), side='right')
print(lad.spice())
