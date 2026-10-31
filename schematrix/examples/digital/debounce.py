# Push-button debounce: pull-up, RC low-pass and a Schmitt-trigger inverter (74HC14).
from schematrix import Schematic

s = Schematic('Switch debounce', description='RC + Schmitt trigger gives one clean edge per press')
s.rail((80, 30), '+5 V')
r1 = s.resistor(anchor='2', at=(80, 30), rot=270, value='10 k\\ohm', ref='R1')      # rot 270: labels on the left
sw = s.switch(anchor='1', at=r1['1'], rot=90, kind='push_no', ref='SW1')
s.wire(r1['1'], (90, 90))
s.gnd(sw['2'])
r2 = s.resistor(anchor='1', at=(90, 90), value='10 k\\ohm', ref='R2')
c1 = s.capacitor(anchor='1', at=(170, 90), rot=90, value='100 nF', ref='C1')
s.wire(r2['2'], (170, 90))
s.gnd(c1['2'])
u = s.schmitt_inverter(anchor='in', at=(260, 90), ref='U1', part='74HC14')
s.wire((170, 90), u['in'])
s.flag(s.wire(u['out'], (u['out'][0] + 30, 90))[-1], '~{BTN}', side='right')
s.note(40, 220, '\\tau = R2 C1 = 1 ms;  the Schmitt thresholds turn the slow RC edge into one clean step')
s.show()
