# RC low-pass step response. tau = R C = 1 ms: the output reaches 63 % of the step at t = tau.
# Run:  schematrix netlist rc-step.py -o rc.cir && ngspice -b rc.cir     (prints the .meas results)
from schematrix import Schematic

s = Schematic('RC step response', description='tau = 1 ms; .meas reports the output at 1 tau and 5 tau')
v1 = s.vsrc(anchor='p', at=(60, 90), rot=90, length=80, kind='pulse', value='PULSE(0 1 0.5m 1n 1n 10m 20m)', ref='V1')
s.gnd(v1['n'])
r1 = s.resistor(anchor='1', at=(60, 60), value='1 k\\ohm', ref='R1')
s.wire(v1['p'], r1['1'])
c1 = s.capacitor(anchor='1', at=(160, 60), rot=90, value='1 \\uF', ref='C1')
s.wire(r1['2'], (160, 60)); s.gnd(c1['2'])
s.flag(s.wire((160, 60), (200, 60))[-1], 'OUT', side='right')
s.directive('.tran 5u 6m', '.meas tran v_tau FIND v(OUT) AT=1.5m', '.meas tran v_5tau FIND v(OUT) AT=5.5m')
s.note(40, 200, 'Expect v_{tau} \\approx 0.632 V,  v_{5tau} \\approx 0.993 V')
s.show()
