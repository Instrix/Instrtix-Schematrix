import pytest

from schematrix import Schematic, netio
from schematrix import geometry as GEO
from schematrix import symbols as SYM
from schematrix.netio import kicad, spice


def amp():
    s = Schematic('amp')
    vin = s.flag((40, 100), 'VIN')
    r = s.resistor((100, 100), value='10 kΩ', fields={'Tolerance': ('1%', True), 'Power': '0.25 W'})
    q = s.npn(anchor='B', at=r['2'], part='BC547')
    s.wire(vin['p'], r['1'])
    s.rail(q['C'], '+5 V')
    s.gnd(q['E'])
    m = s.nmos((300, 100), bulk=True, ref='M1')
    s.wire(q['C'], m['G'])
    s.gnd(m['S']); s.gnd(m['B'])
    return s


def connectivity(nl):
    """nets as sets of (ref, pin), names ignored"""
    return {frozenset(nodes) for nodes in nl.nets().values() if len(nodes) > 1}


@pytest.mark.parametrize('fmt', list(netio.FORMATS))
def test_round_trip(fmt):
    s = amp()
    text = s.export_netlist(fmt)
    back = Schematic.from_netlist(text, fmt)
    a, b = netio.from_doc(s.doc), netio.from_doc(back.doc)
    assert connectivity(a) == connectivity(b)
    for pa in a.parts:
        pb = b.part(pa.ref)
        assert (pb.sym, pb.value, pb.part, pb.props, pb.fields) == (pa.sym, pa.value, pa.part, pa.props, pa.fields)
    assert back.find('R1').fields == {'Tolerance': '1%', 'Power': '0.25 W'}


def test_detect():
    s = amp()
    assert netio.detect(s.export_netlist('kicad')) == 'kicad'
    assert netio.detect(s.export_netlist('json')) == 'json'
    assert netio.detect(s.export_netlist('spice'), 'x.cir') == 'spice'


def test_spice_lines():
    sp = amp().spice()
    assert 'R1 VIN N' in sp and ' 10k' in sp
    line = {ln.split()[0]: ln for ln in sp.splitlines() if ln and not ln.startswith(('*', '.'))}
    assert line['Q1'].endswith(' BC547')
    assert line['M1'].split() == ['M1', 'N001', '+5_V', '0', '0', 'NMOS']        # spaces in net names replaced


FOREIGN_SPICE = """Foreign deck
* a comment
.subckt INNER a b
R9 a b 1k
.ends
R1 in out 1k
C1 out 0 100n ; trailing comment
Q1 c b e 2N3906
M1 d g s sub IRF9540
V1 in 0 SIN(0 1
+ 1k)
X1 in out vcc vee out2 OPAMP
X2 a b c MYCHIP
.model 2N3906 PNP(Bf=200)
.model IRF9540 VDMOS(pchan)
.MODEL irf9540x PMOS
.tran 1u 1m
.end
"""


def test_parse_foreign_spice():
    nl = spice.parse(FOREIGN_SPICE)
    assert nl.title == 'Foreign deck'
    syms = {p.ref: p.sym for p in nl.parts}
    assert syms == {'R1': 'resistor', 'C1': 'capacitor', 'Q1': 'pnp', 'M1': 'pmos', 'V1': 'vsrc', 'X1': 'opamp', 'X2': 'block'}
    assert nl.part('M1').props == {'bulk': True} and nl.part('M1').pins == {'D': 'd', 'G': 'g', 'S': 's', 'B': 'sub'}
    assert nl.part('V1').props == {'kind': 'ac'} and nl.part('V1').value == 'SIN(0 1 1k)'
    assert nl.part('X1').pins == {'inp': 'in', 'inm': 'out', 'vp': 'vcc', 'vn': 'vee', 'out': 'out2'}
    sch = netio.to_schematic(nl)
    assert {frozenset(n) for n in netio.from_doc(sch.doc).nets().values() if len(n) > 1} >= {frozenset({('R1', '2'), ('C1', '1'), ('X1', 'inm')})}


FOREIGN_KICAD = """(export (version "E")
  (design (source "/home/x/board.kicad_sch") (tool "Eeschema 8.0"))
  (components
    (comp (ref "R1") (value "4k7") (footprint "Resistor_SMD:R_0603")
      (fields (field (name "Footprint") "Resistor_SMD:R_0603") (field (name "Tolerance") "1%"))
      (libsource (lib "Device") (part "R") (description "Resistor")))
    (comp (ref "Q1") (value "BC547") (libsource (lib "Device") (part "Q_NPN_CBE")))
    (comp (ref "D1") (value "1N4148") (libsource (lib "Device") (part "D")))
    (comp (ref "J1") (value "Conn") (libsource (lib "Connector") (part "Conn_01x03_Pin")))
    (comp (ref "U1") (value "NE555") (libsource (lib "Timer") (part "NE555P"))))
  (nets
    (net (code "1") (name "/VCC") (node (ref "R1") (pin "1") (pintype "passive")) (node (ref "J1") (pin "1")) (node (ref "U1") (pin "8") (pinfunction "VCC")))
    (net (code "2") (name "Net-(Q1-B)") (node (ref "R1") (pin "2")) (node (ref "Q1") (pin "2") (pinfunction "B")))
    (net (code "3") (name "GND") (node (ref "Q1") (pin "3")) (node (ref "D1") (pin "2")) (node (ref "J1") (pin "3")) (node (ref "U1") (pin "1") (pinfunction "GND")))
    (net (code "4") (name "OUT") (node (ref "Q1") (pin "1")) (node (ref "D1") (pin "1")) (node (ref "J1") (pin "2")))))
"""


def test_parse_foreign_kicad():
    nl = kicad.parse(FOREIGN_KICAD)
    p = {x.ref: x for x in nl.parts}
    assert p['R1'].sym == 'resistor' and p['R1'].value == '4k7' and p['R1'].fields == {'Footprint': 'Resistor_SMD:R_0603', 'Tolerance': '1%'}
    assert p['Q1'].sym == 'npn' and p['Q1'].pins == {'B': 'N001', 'E': 'GND', 'C': 'OUT'}     # CBE order from the name
    assert p['D1'].pins == {'A': 'GND', 'K': 'OUT'}                                          # KiCad D: 1 = K, 2 = A
    assert p['J1'].sym == 'connector' and p['J1'].props['pins'] == 3
    assert p['U1'].sym == 'block' and set(p['U1'].pins) == {'1', '8'}
    sch = netio.to_schematic(nl)
    got = connectivity(netio.from_doc(sch.doc))
    assert frozenset({('R1', '2'), ('Q1', 'B')}) in got
    assert frozenset({('Q1', 'E'), ('D1', 'A'), ('J1', '3'), ('U1', '1')}) in got


def test_fields_in_label_and_svg():
    s = amp()
    r = s.find('R1')
    assert [t for _, _, t, _, _ in GEO.label_block(r.el)] == ['R1', '10 kΩ', '1%']
    r.field('Power', show=True)
    assert '0.25 W' in s.to_svg()
    assert r.field('Power') == '0.25 W'
    r.remove_field('Power')
    assert 'Power' not in r.fields


def test_every_symbol_renders_and_round_trips():
    s = Schematic('all')
    x = 0
    for name, sym in SYM.REGISTRY.items():
        s.add(name, (x, 0)); x += 150
    svg = s.to_svg()
    assert svg.count('<') > 500
    for fmt in netio.FORMATS:
        back = Schematic.from_netlist(s.export_netlist(fmt), fmt)
        got = {c.ref: c.sym for c in back.comps() if SYM.get(c.sym).is_part}
        want = {c.ref: c.sym for c in s.comps() if SYM.get(c.sym).is_part}
        assert got == want, fmt
