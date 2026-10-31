# A figure for a LaTeX paper: 'formal' style (serif, thin lines, italic references) and text markup.
# Export as TikZ (Export -> TikZ, or s.export('fig.tikz')) and \input{fig.tikz} in the document.
from schematrix import Schematic

s = Schematic('Differential amplifier', description='Formal style for papers: export as TikZ or PDF', theme='formal')
u = s.opamp((260, 130), top='-', ref='U_{1}')                    # inm (224, 115), inp (224, 145), out (296, 130)
r1 = s.resistor(anchor='2', at=(190, 115), value='R_{1}', ref='', hide_labels=False)
r3 = s.resistor(anchor='2', at=(190, 145), value='R_{3}', ref='')
s.wire(r1['2'], u['inm']); s.wire(r3['2'], u['inp'])
s.wire((205, 115), (205, 70), (230, 70))
r2 = s.resistor(anchor='1', at=(230, 70), value='R_{2}', ref='')
s.wire(r2['2'], (320, 70), (320, 130))
r4 = s.resistor(anchor='1', at=(205, 145), rot=90, length=60, value='R_{4}', ref='')
s.gnd(r4['2'])
s.flag(s.wire(r1['1'], (100, 115))[-1], 'V_{\\-}', side='left')
s.flag(s.wire(r3['1'], (100, 145))[-1], 'V_{+}', side='left')
s.flag(s.wire(u['out'], (350, 130))[-1], 'V_{out}', side='right')
s.note(100, 250, 'V_{out} = (R_{2} / R_{1}) (V_{+} \\- V_{\\-})   for  R_{2} / R_{1} = R_{4} / R_{3}')
s.show()
