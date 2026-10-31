# Inverting amplifier, gain -R2/R1 = -10, driven by a 1 kHz test tone. Ready to simulate:
#   schematrix netlist inverting-amplifier.py -o amp.cir && ngspice amp.cir
from schematrix import Schematic

s = Schematic('Inverting amplifier', description='Gain -10 op-amp stage, simulated with a 1 kHz sine')
u = s.opamp((240, 100), top='-', ref='U1')                      # inm (204, 85), inp (204, 115), out (276, 100)
r1 = s.resistor(anchor='2', at=(160, 85), value='1 k\\ohm', ref='R1')
s.wire(r1['2'], u['inm'])
s.wire((180, 85), (180, 40))
r2 = s.resistor(anchor='1', at=(200, 40), value='10 k\\ohm', ref='R2')
s.wire((180, 40), r2['1'])
s.wire(r2['2'], (300, 40), (300, 100))
s.wire(u['out'], (330, 100))
s.flag((330, 100), 'V_{OUT}', side='right')
s.gnd(s.wire(u['inp'], (190, 115), (190, 135))[-1])
v1 = s.vsrc(anchor='p', at=(70, 110), rot=90, length=80, kind='ac', ref='V1', value='SIN(0 100m 1k)')
s.wire(v1['p'], (70, 85), r1['1'])
s.gnd(v1['n'])
s.flag((70, 85), 'V_{IN}', side='left')
s.note(40, 245, 'A_{v} = \\-R2 / R1 = \\-10')
s.directive('.tran 10u 3m', '.ac dec 20 10 10Meg')
s.show()
