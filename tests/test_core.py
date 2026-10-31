import io
import json
import os

import pytest

from schematrix import Schematic, symbols as SYM
from schematrix import geometry as GEO
from schematrix.netlist import spice_value, to_spice

HERE = os.path.dirname(__file__)
LEGACY = os.path.join(HERE, '..', 'schematrix', 'examples', 'tr-0002', 'schematics.py')


def rc():
    s = Schematic('rc')
    vin = s.flag((40, 100), 'VIN')
    r = s.resistor((100, 100), value='1 kΩ')
    c = s.capacitor(anchor='1', at=r['2'], rot=90, value='10 nF')
    s.gnd(c['2'])
    s.wire(vin['p'], r['1'])
    w = s.wire(r['2'], (220, 100))
    s.flag(w[-1], 'VOUT', side='right')
    return s, r, c


def test_transform_round_trip():
    for rot in (0, 90, 180, 270):
        for m in (False, True):
            x, y = GEO.xf(3, 7, rot, m)
            assert (abs(x), abs(y)) in ((3, 7), (7, 3))


def test_anchor_places_pin():
    s, r, c = rc()
    assert tuple(c['1']) == tuple(r['2'])


def test_every_symbol_has_geometry():
    for name, sym in SYM.REGISTRY.items():
        g = sym.geometry()
        assert g['prims'] and g['pins'] is not None, name


def test_netlist_and_spice():
    s, r, c = rc()
    nets = s.netlist()['nets']
    assert ('R1', '1') in nets['VIN'] and ('C1', '2') in nets['0']
    assert set(nets['VOUT']) == {('R1', '2'), ('C1', '1')}
    sp = s.spice()
    assert 'R1 VIN VOUT 1k' in sp and 'C1 VOUT 0 10n' in sp


@pytest.mark.parametrize('v,out', [('1 kΩ', '1k'), ('10 mΩ', '10m'), ('4.7 µF', '4.7u'), ('2.2 MΩ', '2.2Meg'), ('30.1k', '30.1k')])
def test_spice_values(v, out):
    assert spice_value(v) == out


def test_junction_on_tee():
    s, r, c = rc()
    assert any(GEO._key(p) == GEO._key(r['2']) for p in GEO.junctions(s.doc))


def test_json_round_trip(tmp_path):
    s, *_ = rc()
    p = s.save(tmp_path / 'x.json')
    s2 = Schematic.load(p)
    assert s2.to_svg() == s.to_svg()


def test_legacy_import_is_pixel_faithful(tmp_path):
    cairosvg = pytest.importorskip('cairosvg')
    np = pytest.importorskip('numpy')
    from PIL import Image
    from schematrix.compat import import_legacy
    import runpy, shutil
    work = tmp_path / 'legacy'
    (work / 'tr-0002-afe1-10-analog-front-end').mkdir(parents=True)
    shutil.copy(LEGACY, work / 'schematics.py')
    cwd = os.getcwd()
    try:
        os.chdir(work)
        runpy.run_path(str(work / 'schematics.py'), run_name='__main__')
    finally:
        os.chdir(cwd)
    figs = import_legacy(str(work / 'schematics.py'))
    assert len(figs) == 12
    for name, sch in figs:
        old = (work / 'tr-0002-afe1-10-analog-front-end' / f'{name}.svg').read_text()
        a = np.asarray(Image.open(io.BytesIO(cairosvg.svg2png(bytestring=old.encode()))).convert('L'), int)
        b = np.asarray(Image.open(io.BytesIO(cairosvg.svg2png(bytestring=sch.to_svg().encode()))).convert('L'), int)
        assert a.shape == b.shape, name
        assert (abs(a - b) > 64).mean() < 0.0005, name


def test_runner_script():
    from schematrix.runner import run
    r = run("from schematrix import Schematic\ns=Schematic('t'); s.resistor((0,0)); print('hi')")
    assert r['ok'] and r['docs'][0]['name'] == 't' and 'hi' in r['stdout']
    bad = run("raise ValueError('boom')")
    assert not bad['ok'] and 'boom' in bad['error']
    slow = run('while True: pass', timeout=2)
    assert not slow['ok'] and 'timed out' in slow['error']


def hop_doc(hops=True):
    s = Schematic('x', hops=hops)
    s.wire((0, 50), (100, 50))           # horizontal, crosses the vertical below
    s.wire((50, 0), (50, 100))
    s.wire((0, 80), (50, 80))            # ends on the vertical: a T junction, never a hop
    return s


def test_hops_only_at_plain_crossings():
    s = hop_doc()
    h = GEO.hops(s.doc)
    assert h == {s.doc['elements'][0]['id']: {0: [(50, 50)]}}
    assert any(GEO._key(p) == (50, 80) for p in GEO.junctions(s.doc))


def test_hop_svg():
    assert GEO.wire_path([(0, 50), (100, 50)], {0: [(50, 50)]}) == 'M0 50L46 50A4 4 0 0 1 54 50L100 50'
    assert GEO.wire_path([(100, 50), (0, 50)], {0: [(50, 50)]}) == 'M100 50L54 50A4 4 0 0 0 46 50L0 50'
    assert 'A4 4' in hop_doc().to_svg() and 'A4 4' not in hop_doc(False).to_svg()


def test_borrows_the_apps_cairo_when_the_system_has_none(tmp_path, monkeypatch):
    import ctypes.util
    import sys
    from schematrix import _cairo
    lib = tmp_path / 'Schematrix.app' / 'Contents' / 'Frameworks' / 'libcairo.2.dylib'
    lib.parent.mkdir(parents=True); lib.write_bytes(b'')
    monkeypatch.setattr(sys, 'platform', 'darwin')
    monkeypatch.delitem(sys.modules, 'cairocffi', raising=False)
    monkeypatch.setattr(ctypes.util, 'find_library', lambda name: None)
    monkeypatch.setattr(_cairo, '_app_cairo', lambda: str(lib))
    _cairo.borrow_app_cairo()
    assert ctypes.util.find_library('cairo-2') == str(lib)
    assert ctypes.util.find_library('png') is None


def test_flag_pad_term_widths_are_their_own_tokens():
    from schematrix import theme as TH
    css = TH.css('instrix')
    assert '.flag { fill: #eef0f4; stroke: #292b31; stroke-width: 1;' in css            # defaults unchanged
    assert '.term { fill: #ffffff; stroke: #292b31; stroke-width: 2.2;' in css
    css = TH.css({'base': 'instrix', 'lw_flag': '1.2', 'lw_pad': '1.4', 'lw_term': '1.8'})
    assert 'stroke-width: 1.2;' in css.split('.flag')[1].split('}')[0]
    assert 'stroke-width: 1.4;' in css.split('.pad')[1].split('}')[0]
    assert 'stroke-width: 1.8;' in css.split('.term')[1].split('}')[0]
    assert '}' not in TH.resolve({'ink': 'red} svg{display:none'})['ink']           # no CSS injection from a document


def test_arrow_head_size_and_ink_colour():
    s = Schematic()
    s.arrow((0, 0), (40, 0), style='', head=(11, 4))
    svg = s.to_svg()
    assert '<polygon class="arrow" points="40,0 29,4 29,-4"/>' in svg                  # ink head, L 11, W 4
    assert 'class="accf"' not in svg.split('</style>')[1]


def test_source_text_and_sized_load():
    from schematrix import geometry as GEO
    s = Schematic()
    v = s.add('vsrc', (0, 0), text='e_{n}')
    g = GEO.geometry(v.el)
    assert any(p['k'] == 'tx' and p['s'] == 'e_{n}' for p in g['prims'])
    assert not any(p['k'] == 'tx' and p['s'] in '+−' for p in g['prims'])               # no polarity signs
    ld = s.add('load', (0, 100), length=40, w=60, h=32, fill='pad')
    box = next(p for p in GEO.geometry(ld.el)['prims'] if p['k'] == 'rc')
    assert (box['w'], box['h'], box['c']) == (60, 32, 'pad')
    assert GEO.geometry(ld.el)['pins']['2'][0] == 30                                     # leads grow to fit the body


def test_compat_turns_raw_markup_into_elements():
    from schematrix.compat import CompatS
    s = CompatS()
    s.add('<rect class="box" x="10" y="20" width="30" height="40" rx="2" style="fill:#dbe8f3"/>')
    s.add('<line class="w" x1="0" y1="0" x2="0" y2="50" stroke-dasharray="2 4"/>')
    s.wire((100, 10), (140, 10))
    s.add('<polygon class="arrow" points="140,6 140,14 150,10"/>')                   # head after the wire's end
    s.add('<polygon class="amp" points="200,89 200,111 222,100"/>')
    s.add('<circle class="pad" cx="226" cy="100" r="4"/>')
    s.add('<circle class="amp" cx="300" cy="100" r="16"/>'); s.text(300, 104, 'eₙ')
    s.wire((300, 60), (300, 84)); s.wire((300, 116), (300, 140))
    s.add('<path d="M0 0"/>')                                                          # unknown: stays raw
    s.svg(400, 200, 't')
    els = s.sch.doc['elements']
    kinds = [e['type'] if e['type'] != 'comp' else e['sym'] for e in els]
    assert kinds.count('raw') == 1 and 'text' not in kinds
    rect = next(e for e in els if e['type'] == 'rect')
    assert rect['cls'] == 'accbox' and not rect.get('css')
    assert next(e for e in els if e['type'] == 'wire' and 'rule' in e['style'])
    arrow = next(e for e in els if e['type'] == 'arrow')
    assert arrow['points'][-1] == [150, 10] and arrow['head'] == [10, 4] and arrow['style'] == ''
    buf = next(e for e in els if e.get('sym') == 'buffer')
    assert (buf['x'], buf['y'], buf['props']['size'], buf['props']['invert']) == (211, 100, 22, True)
    src = next(e for e in els if e.get('sym') == 'vsrc')
    assert src['rot'] == 90 and src['props']['text'] == 'eₙ'


def test_settings_that_change_the_drawing_are_marked_geom():
    """geometry is cached by its geom settings only: a setting that changes the drawing without geom=True is ignored
    (load's label used to always draw LOAD)"""
    import json
    from schematrix import symbols as SYM
    from schematrix.symbols.core import REGISTRY
    shape = lambda g: json.dumps({k: g[k] for k in ('prims', 'pins')}, sort_keys=True)
    wrong = []
    for e in SYM.catalog():
        s = REGISTRY[e['name']]
        for k, spec in e.get('props', {}).items():
            if spec.get('geom') or k in ('ref', 'value', 'part'):
                continue
            d, t = spec.get('default'), spec.get('type')
            alt = (next((c for c in spec.get('choices', []) if c != d), None) if t == 'enum'
                   else float(d or 0) + 7 if t == 'num' else (not d) if t == 'bool' else 'XYZ')
            if alt is not None and shape(s.geometry({})) != shape(s.geometry({k: alt})):
                wrong.append(f'{e["name"]}.{k}')
    assert not wrong, wrong


def test_load_symbol_label_and_load_name():
    """the load's label reaches the drawing, and s.load places the symbol while Schematic.load opens a file"""
    from schematrix import geometry as GEO
    s = Schematic()
    c = s.load((0, 0), label='DUT')
    assert c.sym == 'load' and any(p['k'] == 'tx' and p['s'] == 'DUT' for p in GEO.geometry(c.el)['prims'])


def test_wire_direction_marks_keep_the_wire():
    s = Schematic()
    a = s.resistor((0, 0)); b = s.resistor((200, 0))
    w = s.wire(a['2'], b['1'], marks=[(0, 10, 4)])
    assert w.el['type'] == 'wire'
    assert f'<polygon class="arrow" points="{a["2"][0] + 10:g},0 {a["2"][0]:g},4 {a["2"][0]:g},-4"/>' in s.to_svg()
    assert [('R1', '2'), ('R2', '1')] in s.netlist()['nets'].values()                # still connected


def test_compat_diodes_marks_and_source_arrows():
    from schematrix.compat import CompatS
    s = CompatS()
    s.add('<polygon class="amp" points="140,93 140,107 153,100"/>'); s.wire((153, 93), (153, 107), cls='w plate')
    s.wire((60, 200), (300, 200)); s.add('<polygon class="arrow" points="60,196 60,204 70,200"/>')   # a marker
    s.add('<circle class="amp" cx="130" cy="300" r="16"/>')
    s.add('<polygon class="arrow" points="124,296 124,304 135,300"/>'); s.wire((120, 300), (130, 300))
    s.svg(400, 400, 't')
    els = s.sch.doc['elements']
    assert not [e for e in els if e['type'] == 'raw']
    d = next(e for e in els if e.get('sym') == 'diode')
    assert (d['x'], d['y'], d['rot']) == (147, 100, 0) and not [e for e in els if 'plate' in e.get('style', '')]
    assert next(e for e in els if e.get('marks'))['marks'] == [[0, 10, 4]]
    src = next(e for e in els if e.get('sym') == 'isrc')['props']
    assert (src['arrow_tail'], src['arrow_tip'], src['arrow_len'], src['arrow_w']) == (-10, 5, 11, 4)
