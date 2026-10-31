from schematrix import Schematic, netio
from schematrix.netlist import bus_members, extract


def bus_sheet():
    """an 8-bit register whose Q bus runs right, labelled Q[7:0]; bit 3 taps off through a bus entry to an LED"""
    s = Schematic('bus')
    reg = s.register8((100, 40), bus=True, oe=False, ref='U1')
    q = reg['Q']
    s.wire(q, (q[0] + 120, q[1]), style='bus')
    s.flag((q[0] + 120, q[1]), 'Q[7:0]', side='right')
    e = s.busentry((q[0] + 60, q[1]), direction='down')
    s.flag(s.wire(e['bit'], (e['bit'][0], e['bit'][1] + 30))[-1], 'Q3', side='right')
    led = s.led(anchor='A', at=(q[0] + 150, q[1] + 120), rot=90, ref='D1')
    s.flag(led['A'], 'Q3', side='left')
    s.gnd(led['K'])
    s.flag(s.wire(reg['D'], (reg['D'][0] - 40, reg['D'][1]), style='bus')[-1], 'DATA[7:0]', side='left')
    return s, reg, led


def test_bus_names():
    assert bus_members('D[7:0]') == ('D', list(range(8)))
    assert bus_members('A[0..3]') == ('A', [0, 1, 2, 3])
    assert bus_members('CLK') == ('CLK', None)


def test_bus_pins_connect_bit_by_bit():
    s, reg, led = bus_sheet()
    nx = extract(s.doc)
    assert nx['nets']['Q3'] == [('D1', 'A'), ('U1', 'Q3')] or sorted(nx['nets']['Q3']) == [('D1', 'A'), ('U1', 'Q3')]
    assert nx['pins'][(reg.id, 'D7')] == 'DATA7' and nx['pins'][(reg.id, 'Q0')] == 'Q0'
    assert not any('Q[7:0]' in n for n in nx['nets'])
    assert not [w for w in nx['warnings'] if 'bits wide' in w]


def test_plain_wire_touching_a_bus_does_not_join_it():
    s, reg, led = bus_sheet()
    q = reg['Q']
    s.wire((q[0] + 90, q[1]), (q[0] + 90, q[1] - 40))           # ends on the bus without an entry or label
    nx = extract(s.doc)
    assert all(n.startswith(('Q', 'DATA', 'N', '0')) for n in nx['nets'])
    assert len(nx['nets']['Q3']) == 2


def test_width_mismatch_warns():
    s = Schematic('m')
    reg = s.register8((100, 40), bus=True, oe=False)
    s.flag(s.wire(reg['Q'], (reg['Q'][0] + 60, reg['Q'][1]), style='bus')[-1], 'Q[3:0]', side='right')
    assert any('8 bits wide but its bus Q[3:0] has 4' in w for w in extract(s.doc)['warnings'])


def test_unlabelled_bus_between_two_parts():
    s = Schematic('u')
    a = s.register8((100, 40), bus=True, oe=False, ref='U1')
    b = s.register8((300, 40), bus=True, oe=False, ref='U2')
    s.wire(a['Q'], (a['Q'][0] + 20, a['Q'][1]), (a['Q'][0] + 20, b['D'][1]), b['D'], style='bus')
    nets = extract(s.doc)['nets']
    joined = [n for n, m in nets.items() if ('U1', 'Q5') in m]
    assert joined and ('U2', 'D5') in nets[joined[0]]


def test_bus_parts_survive_netlist_round_trips():
    s, *_ = bus_sheet()
    for fmt in netio.FORMATS:
        back = Schematic.from_netlist(s.export_netlist(fmt), fmt)
        a = {frozenset(m) for m in netio.from_doc(s.doc).nets().values() if len(m) > 1}
        b = {frozenset(m) for m in netio.from_doc(back.doc).nets().values() if len(m) > 1}
        assert a == b, fmt
