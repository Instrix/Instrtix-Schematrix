# Second-order Sallen-Key low-pass, unity gain, f_c ~ 1 kHz, Q ~ 0.71 (Butterworth). Simulate the .ac sweep.
from schematrix import Schematic

s = Schematic('Sallen-Key low-pass', description='2nd-order Butterworth, f_c = 1 kHz')
u = s.opamp((350, 115), top='+', ref='U1')                      # inp (314, 100), inm (314, 130), out (386, 115)
v1 = s.vsrc(anchor='p', at=(40, 130), rot=90, length=80, kind='ac', ref='V1', value='AC 1')
s.gnd(v1['n'])
r1 = s.resistor(anchor='1', at=(70, 100), value='11.3 k\\ohm', ref='R1')     # ends at (130, 100)
r2 = s.resistor(anchor='1', at=(160, 100), value='11.3 k\\ohm', ref='R2')    # (160, 100) -> (220, 100)
s.wire(v1['p'], (40, 100), r1['1'])
s.wire(r1['2'], (145, 100), r2['1'])                            # node A at x = 145
s.wire((145, 100), (145, 45), (180, 45))                        # C1 from node A ...
c1 = s.capacitor(anchor='1', at=(180, 45), length=80, value='20 nF', ref='C1')
s.wire(c1['2'], (420, 45), (420, 115))                          # ... to the output
s.wire(r2['2'], u['inp'])                                       # node B
c2 = s.capacitor(anchor='1', at=(245, 100), rot=90, value='10 nF', ref='C2')
s.gnd(c2['2'])
s.wire(u['out'], (450, 115))
s.flag((450, 115), 'OUT', side='right')
s.wire(u['inm'], (302, 130), (302, 175), (420, 175), (420, 115))   # unity-gain feedback
s.note(40, 255, 'f_{c} = 1 / (2\\pi \\sqrt{}(R1 R2 C1 C2)) \\approx 1 kHz,  Q = 0.71')
s.directive('.ac dec 50 10 100k')
s.show()
