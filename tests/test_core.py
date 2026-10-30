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
