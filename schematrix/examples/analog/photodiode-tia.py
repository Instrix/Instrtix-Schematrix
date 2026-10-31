# Photodiode transimpedance amplifier: V_out = I_ph x R_F; C_F keeps the loop stable.
from schematrix import Schematic

s = Schematic('Photodiode TIA', description='Zero-bias photodiode, 1 MOhm transimpedance')
u = s.opamp((260, 160), top='-', ref='U1', part='OPA380')       # inm (224, 145), inp (224, 175), out (296, 160)
pd = s.photodiode(anchor='K', at=(150, 145), rot=270, ref='D1', part='BPW34')
s.gnd(pd['A'])
s.wire(pd['K'], u['inm'])
s.gnd(s.wire(u['inp'], (210, 175), (210, 195))[-1])
s.wire((190, 145), (190, 80), (220, 80))
rf = s.resistor(anchor='1', at=(220, 80), value='1 M\\ohm', ref='R_{F}')
s.wire(rf['2'], (320, 80), (320, 160))
s.wire((190, 80), (190, 20), (230, 20))
cf = s.capacitor(anchor='1', at=(230, 20), value='2.2 pF', ref='C_{F}')
s.wire(cf['2'], (320, 20), (320, 80))
s.wire(u['out'], (350, 160))
s.flag((350, 160), 'V_{OUT}', side='right')
s.note(60, 265, 'V_{OUT} = I_{ph} \\times R_{F}    (1 \\uA \\to 1 V)')
s.show()
