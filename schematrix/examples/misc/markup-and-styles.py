# The same small circuit in every drawing style, with text markup in labels, values and notes.
from schematrix import Schematic, theme

for name in theme.THEMES:
    s = Schematic(f'Style: {name}', theme=name)
    q = s.nmos((160, 90), ref='Q_{1}', part='IRLML6244', fields={'R_{DS(on)}': ('21 m\\ohm', True)})
    s.rail((160, 20), 'V_{DD}')
    rl = s.resistor(anchor='1', at=(160, 20), rot=90, length=40, body=24, value='4.7 k\\ohm \\pm1 %', ref='R_{L}')
    s.wire(rl['2'], q['D'])
    s.gnd(q['S'])
    s.flag(s.wire(q['G'], (90, 90))[-1], '~{EN}', side='left')
    s.note(40, 170, 'I_{D} \\approx 2.5 mA,  V_{GS(th)} \\le 1.1 V,  T_{j} \\le 150 \\deg{}C')
    s.show()
