import pytest

from schematrix import Schematic, netio
from schematrix import geometry as GEO
from schematrix import symbols as SYM
from schematrix.netio import kicad
from schematrix.symbols.logic_block import parse


def test_presets_are_methods_and_store_the_base_symbol():
    s = Schematic('p')
    z = s.zener((0, 0), value='5V1')
    assert (z.sym, z.props['kind'], z.ref) == ('diode', 'zener', 'D1')
    g = s.nand_gate((100, 0), inputs=3)
    assert (g.sym, g.props) == ('gate', {'kind': 'nand', 'inputs': 3, 'ref': 'U1'})
    assert s.not_gate((200, 0)).props['invert'] is True
    with pytest.raises(AttributeError):
        s.no_such_part


@pytest.mark.parametrize('key', sorted(SYM.PRESETS))
def test_every_preset_renders(key):
    sym, props = SYM.resolve(key)
    g = SYM.get(sym).geometry(props)
    assert g['pins'] and g['prims']


def test_catalog_lists_presets():
    cat = {e['name']: e for e in SYM.catalog()}
    names = {p['name'] for p in cat['diode']['presets']}
    assert {'zener', 'schottky', 'led', 'tvs_diode', 'pin_diode', 'varactor'} <= names
    assert {p['name'] for p in cat['gate']['presets']} == {'and_gate', 'nand_gate', 'or_gate', 'nor_gate', 'xor_gate', 'xnor_gate'}


def test_kicad_aliases_pick_the_variant():
    assert SYM.by_alias('74HC00') == ('gate', {'kind': 'nand'})
    assert SYM.by_alias('D_Zener') == ('diode', {'kind': 'zener'})
    assert SYM.by_alias('74HC595') == ('shiftreg', {})
    s = Schematic('k')
    s.zener((0, 0)); s.nor_gate((100, 0))
    text = s.export_netlist('kicad')
    assert '(part "D_Zener")' in text and '(part "74HC02")' in text
    nl = kicad.parse(text.replace('schematrix_symbol', 'x').replace('schematrix_props', 'y'))   # as if from KiCad
    assert {(p.sym, p.props.get('kind')) for p in nl.parts} == {('diode', 'zener'), ('gate', 'nor')}


def test_gate_inputs_inversion_and_iec():
    s = Schematic('g')
    g = s.and_gate((0, 0), inputs=16, invert_inputs='1, 16')
    pins = GEO.geometry(g.el)['pins']
    assert len([p for p in pins if p.startswith('in')]) == 16
    bubbles = [p for p in GEO.geometry(g.el)['prims'] if p['k'] == 'ci']
    assert len(bubbles) == 2
    iec = s.xor_gate((200, 0), shape='iec')
    assert any(p['k'] == 'tx' and p['s'] == '=1' for p in GEO.geometry(iec.el)['prims'])


def test_bus_pins_or_one_per_bit():
    s = Schematic('b')
    r = s.register((0, 0), bits=8, bus=True)
    assert {'D', 'Q', 'CLK', 'OE'} <= set(r.pins)
    r2 = s.register((200, 0), bits=8)
    assert {f'D{i}' for i in range(8)} | {f'Q{i}' for i in range(8)} <= set(r2.pins)
    assert any('bus' in p['c'] for p in GEO.geometry(r.el)['prims'])


def test_logic_block_pin_spec():
    ps = parse('D[8], , ~>CLK, ~OE')
    assert [p and (p['name'], p['width'], p['neg'], p['clk']) for p in ps] == \
        [('D', 8, False, False), None, ('CLK', 1, True, True), ('OE', 1, True, False)]
    assert [p['name'] for p in parse('A[3]', bus=False)] == ['A0', 'A1', 'A2']
    s = Schematic('ic')
    u = s.logic_ic((0, 0), left='A[4], B[4], , CI', right='S[4], , CO', top='VCC', bottom='GND')
    assert set(u.pins) == {'A', 'B', 'CI', 'S', 'CO', 'VCC', 'GND'}
    for x, y in u.pins.values():
        assert x % 5 == 0 and y % 5 == 0


def test_presets_survive_netlist_round_trips():
    s = Schematic('rt')
    x = 0
    for key in sorted(SYM.PRESETS):
        s.add(key, (x, 0)); x += 200
    for fmt in netio.FORMATS:
        back = Schematic.from_netlist(s.export_netlist(fmt), fmt)
        want = {c.ref: (c.sym, {k: v for k, v in c.props.items() if k != 'ref'}) for c in s.comps()}
        got = {c.ref: (c.sym, {k: v for k, v in c.props.items() if k != 'ref'}) for c in back.comps() if c.ref in want}
        assert got == want, fmt
