"""Documentation-figure features: timing diagrams, annotations, auto-routing."""
from schematrix import Schematic
from schematrix import geometry as GEO
from schematrix.route import route
from schematrix.symbols import timing as TIMING


def test_timing_description_and_drawing():
    rows = TIMING.parse('CLK : p...\n\nDATA: x=.=x | A5 3C\nEN: 0.1.')
    assert rows[0] == ('CLK', 'p...', []) and rows[1] is None and rows[2] == ('DATA', 'x=.=x', ['A5', '3C'])
    s = Schematic()
    td = s.timing((0, 0), signals='CLK : p...\nDATA: x=.=x | A5 3C\nEN  : 0.1.|.0', grid=True)
    g = GEO.geometry(td.el)
    texts = [p['s'] for p in g['prims'] if p['k'] == 'tx']
    assert {'CLK', 'DATA', 'EN', 'A5', '3C'} <= set(texts)
    assert any(p.get('c') == 'tdata' for p in g['prims']) and any(p.get('c') == 'gap' for p in g['prims'])
    clk = next(p for p in g['prims'] if p['k'] == 'pl' and p['pts'][0][1] == 15 - 7)     # the clock starts high
    assert len(clk['pts']) == 1 + 4 * 3 + 3                                                 # 4 periods, vertical edges


def test_annotations_are_drawings_not_parts():
    s = Schematic()
    r = s.resistor((0, 0))
    s.brace((0, -20), length=60, text='$R_{in}$'); s.callout((40, -30), number='1')
    s.dimension((0, 40), length=60, text='5 mm'); s.highlight((0, 0), w=70, h=30)
    s.timing((0, 80))
    nl = s.netlist()
    assert {ref for pins in nl['nets'].values() for ref, _ in pins} == {r.ref}
    svg = s.to_svg()
    assert 'class="hl"' in svg and 'class="callacc"' in svg


def test_autoroute_goes_around_parts_and_never_through_pins():
    s = Schematic()
    u = s.opamp((200, 100))
    r = s.resistor((60, 100))
    other = s.resistor((200, 30))
    pts = route(s.doc, r['1'], u['out'])
    body = GEO.geometry(u.el)['bbox']
    x0, y0 = GEO.place(u.el, body[0], body[1]); x1, y1 = GEO.place(u.el, body[2], body[3])
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        assert ax == bx or ay == by                                   # orthogonal
        for t in (i / 20 for i in range(21)):
            px, py = ax + (bx - ax) * t, ay + (by - ay) * t
            assert not (min(x0, x1) < px < max(x0, x1) and min(y0, y1) < py < max(y0, y1))
    for p in list(other.pins.values()) if hasattr(other, 'pins') else [other['1'], other['2']]:
        assert tuple(p) not in [tuple(q) for q in pts]
    w = s.autoroute(r['1'], u['out'])
    assert [tuple(p) for p in w.el['points']] == [tuple(p) for p in pts]
