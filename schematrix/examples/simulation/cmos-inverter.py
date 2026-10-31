# CMOS inverter DC transfer curve: sweep the input 0..5 V and find the switching threshold.
from schematrix import Schematic

s = Schematic('CMOS inverter', description='Complementary pair; .dc sweep and switching threshold')
vdd = s.vsrc(anchor='p', at=(320, 70), rot=90, length=80, value='5', ref='V2')
s.rail(vdd['p'], 'VDD'); s.gnd(vdd['n'])
p1 = s.pmos(anchor='D', at=(180, 110), rot=180, mirror=True, ref='M1')   # source up to VDD, drain down
n1 = s.nmos(anchor='D', at=(180, 110), ref='M2')                          # drain up, source to ground
s.rail(p1['S'], 'VDD'); s.gnd(n1['S'])
s.wire(p1['G'], (130, p1['G'][1]), (130, n1['G'][1]), n1['G'])
vin = s.vsrc(anchor='p', at=(60, 130), rot=90, length=80, value='0', ref='V1')
s.gnd(vin['n'])
s.wire(vin['p'], (60, 110), (130, 110))
s.flag(s.wire((180, 110), (240, 110))[-1], 'OUT', side='right')
s.flag((60, 110), 'IN', side='left')
s.directive('.dc V1 0 5 0.01', '.meas dc vth WHEN v(OUT)=2.5')
s.note(40, 260, 'Symmetric thresholds put V_{th} near V_{DD}/2 when K_{p,n}/K_{p,p} matches the mobility ratio')
s.show()
