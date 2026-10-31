# SR latch from two cross-coupled NAND gates. Wire hops make the crossing feedback wires readable.
from schematrix import Schematic

s = Schematic('SR latch (NAND)', description='Active-low set / reset latch', hops=True)
g1 = s.nand_gate((200, 80), ref='U1')       # in1 (165, 70), in2 (165, 90), out (233, 80)
g2 = s.nand_gate((200, 180), ref='U2')      # in1 (165, 170), in2 (165, 190), out (233, 180)
s.wire(g1['out'], (250, 80), (250, 125), (150, 125), (150, 170), g2['in1'])
s.wire(g2['out'], (265, 180), (265, 140), (135, 140), (135, 90), g1['in2'])
s.flag(s.wire((250, 80), (300, 80))[-1], 'Q', side='right')
s.flag(s.wire((265, 180), (300, 180))[-1], '~{Q}', side='right')
s.flag(s.wire(g1['in1'], (90, 70))[-1], '~{S}', side='left')
s.flag(s.wire(g2['in2'], (90, 190))[-1], '~{R}', side='left')
s.note(90, 240, '~{S} = 0 sets Q,  ~{R} = 0 resets it,  both 1 holds')
s.show()
