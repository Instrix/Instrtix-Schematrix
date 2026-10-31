# High-side load switch: P-MOSFET with an NPN level shifter so a 3.3 V signal can switch 12 V.
from schematrix import Schematic

s = Schematic('High-side load switch', description='P-FET switch, NPN gate pull-down, gate pull-up')
q1 = s.pmos(anchor='S', at=(170, 40), rot=90, mirror=True, ref='Q1', part='AO3401', body_diode=True)
s.flag(s.wire(q1['S'], (120, 40))[-1], 'V_{IN} 12 V', side='left')
s.flag(s.wire(q1['D'], (320, 40))[-1], 'V_{LOAD}', side='right')
r1 = s.resistor(anchor='1', at=(150, 40), rot=90, value='100 k\\ohm', ref='R1')
s.wire(r1['2'], (150, 120), (q1['G'][0], 120), q1['G'])
q2 = s.npn(anchor='C', at=(q1['G'][0], 150), ref='Q2', part='BC817')
s.wire((q1['G'][0], 120), q2['C'])
s.gnd(q2['E'])
r2 = s.resistor(anchor='2', at=q2['B'], value='10 k\\ohm', ref='R2')
s.flag(s.wire(r2['1'], (r2['1'][0] - 20, r2['1'][1]))[-1], 'EN', side='left')
s.note(40, 260, 'EN high \\to Q2 on \\to gate pulled low \\to Q1 on (V_{GS} = \\-12 V; check V_{GS(max)})')
s.show()
