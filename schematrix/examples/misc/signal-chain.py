# A measurement signal chain as a block diagram: sensor, amplifier, anti-alias filter, ADC, processor.
from schematrix import Schematic

s = Schematic('Signal chain', description='Block diagram with signal-flow symbols')
sen = s.sensor((40, 100), quantity='T', ref='S1', value='PT100')
amp = s.amplifier(anchor='in', at=(sen['2'][0] + 30, 100), gain='\\times 50', ref='A1', value='PGA')
s.wire(sen['2'], amp['in'])
flt = s.filter(anchor='in', at=(amp['out'][0] + 30, 100), kind='lp', ref='FL1', value='f_{c} = 1 kHz')
s.wire(amp['out'], flt['in'])
adc = s.converter(anchor='in', at=(flt['out'][0] + 30, 100), src='A', dst='D', ref='U1', value='24 bit')
s.wire(flt['out'], adc['in'])
mcu = s.block(at=(adc['out'][0] + 40, 70), w=110, h=60, title='MCU', pins='IN:l, UART:r', ref='U2', show_pins=False)
s.wire(adc['out'], mcu['IN'], style='bus')
s.flag(s.wire(mcu['UART'], (mcu['UART'][0] + 30, mcu['UART'][1]))[-1], 'TX', side='right')
s.arrow((60, 40), (500, 40)); s.note(60, 32, 'signal flow')
s.note(60, 170, 'Sampled at f_{s} = 8 kS/s; the filter keeps everything above f_{s}/2 out of the ADC')
s.show()
