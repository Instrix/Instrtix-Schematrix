"""Digital building blocks: registers and latches, shift registers, counters, decoders, encoders, demultiplexers,
adders, magnitude comparators, and a fully custom logic IC. All share the logic-block engine (logic_block.py):
widths are properties, and every multi-bit port is either one bus pin or one pin per bit ('Bus pins')."""
from __future__ import annotations

import math

from .core import ENUM, FLAG, G, Prop, symbol
from .logic_block import block, bus_pins, parse, pin


def _n(v, lo=1, hi=64):
    return max(lo, min(hi, int(float(v))))


BITS = lambda d, label='Bits': Prop(d, 'num', True, label=label, help='port width in bits')
BUS = FLAG(False, 'Bus pins', help='one thick bus pin per port instead of one pin per bit')


def _g(*args, **kw):
    prims, pins, label = block(*args, **kw)
    return G(prims, pins, label)


@symbol('register', 'Register / latch array', 'Logic', 'U', None,
        {'bits': BITS(8), 'kind': ENUM('flip-flop', ['flip-flop', 'latch'], 'Kind'), 'bus': BUS,
         'oe': FLAG(True, 'Output enable'), 'clear': FLAG(False, 'Clear')},
        presets=(('register8', 'Register (D flip-flops)', {}, ('74HC574', '74HC374', '74HC273')),
                 ('latch8', 'Transparent latch', {'kind': 'latch'}, ('74HC573', '74HC373'))))
def register(p):
    n, bus, latch = _n(p['bits']), p['bus'], p['kind'] == 'latch'
    left = bus_pins('D', n, bus) + [None, pin('LE') if latch else pin('CLK', 'CLK', clk=True)]
    if p['clear']:
        left.append(pin('CLR', neg=True))
    if p['oe']:
        left.append(pin('OE', neg=True))
    return _g(f'{"LATCH" if latch else "REG"}{n}', left, bus_pins('Q', n, bus))


@symbol('shiftreg', 'Shift register', 'Logic', 'U', None,
        {'bits': BITS(8), 'mode': ENUM('sipo', ['sipo', 'piso', 'siso', 'pipo'], 'Mode',
                                       help='serial / parallel in, serial / parallel out'),
         'bus': BUS, 'clear': FLAG(True, 'Clear'), 'oe': FLAG(False, 'Output enable')},
        presets=(('shiftreg_sipo', 'Shift register, serial in / parallel out', {}, ('74HC595', '74HC164', '74HC4094')),
                 ('shiftreg_piso', 'Shift register, parallel in / serial out', {'mode': 'piso'}, ('74HC165', '74HC166')),
                 ('shiftreg_universal', 'Shift register, universal', {'mode': 'pipo', 'bits': 4}, ('74HC194', '74HC299'))))
def shiftreg(p):
    n, bus, mode = _n(p['bits']), p['bus'], p['mode']
    pin_in, pout = mode[0] == 'p', mode[2] == 'p'
    left = [pin('SER')]
    if pin_in:
        left = bus_pins('D', n, bus) + [None, pin('SER'), pin('LD', neg=True)]
    left.append(pin('CLK', 'CLK', clk=True))
    if p['clear']:
        left.append(pin('CLR', neg=True))
    if p['oe'] and pout:
        left.append(pin('OE', neg=True))
    right = (bus_pins('Q', n, bus) + [None] if pout else []) + [pin('QS')]
    return _g(f'SRG{n}', left, right)


@symbol('counter', 'Counter', 'Logic', 'U', None,
        {'bits': BITS(4), 'direction': ENUM('up', ['up', 'updown'], 'Direction'), 'load': FLAG(True, 'Parallel load'),
         'enable': FLAG(True, 'Count enable'), 'clear': FLAG(True, 'Clear'), 'carry': FLAG(True, 'Carry out'), 'bus': BUS},
        presets=(('counter4', 'Counter, binary', {}, ('74HC161', '74HC163', '74HC160')),
                 ('counter_updown', 'Counter, up / down', {'direction': 'updown'}, ('74HC191', '74HC193', '74HC190')),
                 ('ripple_counter', 'Ripple counter', {'bits': 12, 'load': False, 'enable': False, 'carry': False},
                  ('74HC4040', 'CD4040', '74HC393', '74HC4060'))))
def counter(p):
    n, bus = _n(p['bits']), p['bus']
    left = []
    if p['load']:
        left += bus_pins('D', n, bus) + [None, pin('LD', neg=True)]
    if p['enable']:
        left.append(pin('EN'))
    if p['direction'] == 'updown':
        left.append(pin('UD', 'U/D'))
    left.append(pin('CLK', 'CLK', clk=True))
    if p['clear']:
        left.append(pin('CLR', neg=True))
    right = bus_pins('Q', n, bus)
    if p['carry']:
        right += [None, pin('CO')]
    return _g(f'CTR{n}', left, right)


@symbol('decoder', 'Decoder / demultiplexer', 'Logic', 'U', None,
        {'inputs': Prop(3, 'num', True, label='Address bits', help='1 to 5: 2, 4, 8, 16 or 32 outputs'),
         'active_low': FLAG(True, 'Active-low outputs'), 'enable': FLAG(True, 'Enable'), 'bus': BUS},
        presets=(('decoder_2to4', 'Decoder 2:4', {'inputs': 2}, ('74HC139',)),
                 ('decoder_3to8', 'Decoder 3:8', {}, ('74HC138', '74HC238')),
                 ('decoder_4to16', 'Decoder 4:16', {'inputs': 4}, ('74HC154', 'CD4514'))))
def decoder(p):
    k = _n(p['inputs'], 1, 5)
    left = bus_pins('A', k, p['bus'])
    if p['enable']:
        left += [None, pin('E', neg=True)]
    right = [pin(f'Y{i}', neg=p['active_low']) for i in range(2 ** k)]
    return _g(f'{k}:{2 ** k} DEC', left, right)


@symbol('encoder', 'Priority encoder', 'Logic', 'U', None,
        {'outputs': Prop(3, 'num', True, label='Output bits', help='1 to 5: 2, 4, 8, 16 or 32 inputs'),
         'active_low': FLAG(True, 'Active-low'), 'enable': FLAG(True, 'Enable in / out'), 'bus': BUS},
        presets=(('priority_encoder', 'Priority encoder 8:3', {}, ('74HC148', 'CD4532')),))
def encoder(p):
    k, low = _n(p['outputs'], 1, 5), p['active_low']
    left = [pin(f'I{i}', neg=low) for i in range(2 ** k)]
    if p['enable']:
        left += [None, pin('EI', neg=low)]
    right = bus_pins('A', k, p['bus'], neg=low)
    if p['enable']:
        right += [None, pin('GS', neg=low), pin('EO', neg=low)]
    return _g(f'{2 ** k}:{k} ENC', left, right)


@symbol('demux', 'Demultiplexer (data)', 'Logic', 'U', None,
        {'outputs': ENUM(4, [2, 4, 8, 16], 'Outputs'), 'width': Prop(1, 'num', True, label='Data width', help='bits per port'),
         'enable': FLAG(True, 'Enable'), 'bus': BUS})
def demux(p):
    n, w = int(p['outputs']), _n(p['width'])
    k = int(math.log2(n))
    left = bus_pins('D', w, True) + [None] + bus_pins('S', k, p['bus'])
    if p['enable']:
        left.append(pin('E', neg=True))
    right = []
    for i in range(n):
        right += bus_pins(f'Y{i}', w, True)
    return _g('DMUX', left, right)


@symbol('adder', 'Adder', 'Logic', 'U', None,
        {'bits': BITS(4), 'carry_in': FLAG(True, 'Carry in'), 'carry_out': FLAG(True, 'Carry out'), 'bus': BUS},
        presets=(('adder4', 'Adder, 4-bit', {}, ('74HC283', '74LS283')),))
def adder(p):
    n, bus = _n(p['bits']), p['bus']
    left = bus_pins('A', n, bus) + [None] + bus_pins('B', n, bus)
    if p['carry_in']:
        left += [None, pin('CI')]
    right = bus_pins('S', n, bus)
    if p['carry_out']:
        right += [None, pin('CO')]
    return _g('Σ', left, right)


@symbol('magcomp', 'Magnitude comparator', 'Logic', 'U', None,
        {'bits': BITS(4), 'cascade': FLAG(False, 'Cascade inputs'), 'bus': BUS},
        presets=(('magnitude_comparator', 'Magnitude comparator', {}, ('74HC85', '74HC688')),))
def magcomp(p):
    n, bus = _n(p['bits']), p['bus']
    left = bus_pins('A', n, bus) + [None] + bus_pins('B', n, bus)
    if p['cascade']:
        left += [None, pin('ILT', '<'), pin('IEQ', '='), pin('IGT', '>')]
    right = [pin('LT', 'A<B'), pin('EQ', 'A=B'), pin('GT', 'A>B')]
    return _g('COMP', left, right)


@symbol('logic_ic', 'Logic IC (custom)', 'Logic', 'U', None,
        {'title': Prop('IC', 'str', True, label='Function', help='text inside the top of the body'),
         'left': Prop('D[8], , >CLK, ~OE', 'str', True, label='Left pins'),
         'right': Prop('Q[8]', 'str', True, label='Right pins'),
         'top': Prop('', 'str', True, label='Top pins'),
         'bottom': Prop('', 'str', True, label='Bottom pins'),
         'bus': FLAG(True, 'Bus pins', help='off: expand D[8] into D0..D7'),
         'min_width': Prop(40, 'num', True, label='Min width')},
        help='pins: comma list; ~ = active low (bubble), > = clock, [n] = n-bit bus, empty item = gap')
def logic_ic(p):
    bus = p['bus']
    return _g(str(p['title']), parse(p['left'], bus), parse(p['right'], bus), parse(p['top'], bus),
              parse(p['bottom'], bus), min_w=float(p.get('min_width') or 40))
