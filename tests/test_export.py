import os
import shutil
import subprocess

import pytest

from schematrix import Schematic, export as EX, markup as MU, netio, runner
from schematrix.units import spice_value

HERE = os.path.dirname(__file__)


def small():
    s = Schematic('t', theme='formal')
    r = s.resistor((100, 60), value='4.7 k\\ohm', ref='R_{1}')
    c = s.capacitor(anchor='1', at=r['2'], rot=90, value='10 \\uF', ref='C1')
    s.gnd(c['2'])
    s.text(20, 120, '~{OE}  V_{CC}  x^{2}', 'lbl')
    return s, r, c


# ---------------------------------------------------------------- markup
@pytest.mark.parametrize('src,plain', [
    ('10 k\\ohm', '10 kΩ'), ('4.7 \\uF', '4.7 µF'), ('~{RST}', 'RST'), ('R_{DS(on)}', 'RDS(on)'), ('x^{2}', 'x2'),
    ('f_c', 'f_c'), ('a\\{b\\}', 'a{b}'), ('\\foo', '\\foo'), ('25 \\deg{}C', '25 °C'), ('\\-5', '−5'), ('\\pm1 %', '±1 %')])
def test_markup_plain(src, plain):
    assert MU.plain(src) == plain


def test_markup_runs_and_svg():
    assert MU.parse('~{CS_{1}} x') == [('CS', frozenset({'over'})), ('1', frozenset({'over', 'sub'})), (' x', frozenset())]
    svg = MU.svg_inner('V_{CC}', 12, lambda t: t)
    assert svg.startswith('V<tspan dy="3.84"') and 'font-size:8.64px' in svg
    assert spice_value('10 k\\ohm') == '10k'


def test_markup_matches_js_twin():
    node = shutil.which('node')
    if not node:
        pytest.skip('node not installed')
    js = os.path.join(HERE, '..', 'schematrix', 'web', 'js', 'markup.js')
    cases = ['10 k\\ohm', '~{CS_{1}} x', 'V_{CC} = 3 V', '\\uF', 'a\\{b\\}']
    code = (f"import * as M from '{os.path.abspath(js)}';"
            f"for (const s of {cases!r}) console.log(M.svgInner(s, 12, (t) => t));")
    out = subprocess.run([node, '--input-type=module', '-e', code], capture_output=True, text=True, check=True).stdout.splitlines()
    assert out == [MU.svg_inner(s, 12, lambda t: t) for s in cases]


# ---------------------------------------------------------------- exports
def test_svg_background_and_selection_crop():
    s, r, c = small()
    full = EX.export(s.doc, 'svg', background=True)[0].decode()
    clear = EX.export(s.doc, 'svg', background=False)[0].decode()
    assert 'fill="#ffffff"' in full and '<rect x=' not in clear.split('</style>')[1][:200]
    part = EX.export(s.doc, 'svg', ids=[r.id], margin=5)[0].decode()
    vb_full = [float(v) for v in full.split('viewBox="')[1].split('"')[0].split()]
    vb_part = [float(v) for v in part.split('viewBox="')[1].split('"')[0].split()]
    assert vb_part[2] < vb_full[2] and vb_part[3] < vb_full[3]
    with pytest.raises(EX.ExportError):
        EX.export(s.doc, 'svg', ids=['nope'])


@pytest.mark.parametrize('fmt,magic', [('png', b'\x89PNG'), ('jpeg', b'\xff\xd8'), ('webp', b'RIFF'), ('pdf', b'%PDF'),
                                       ('eps', b'%!PS')])
def test_bitmap_and_vector_formats(fmt, magic):
    pytest.importorskip('cairosvg'); pytest.importorskip('PIL')
    s, *_ = small()
    assert EX.export(s.doc, fmt, background=False)[0][:len(magic)] == magic


def test_cairo_overbars_become_lines():
    s, *_ = small()
    svg = EX.svg_of(s.doc, fonts=False)
    out = EX.for_cairo(svg, s.doc['theme'])
    assert 'overline' not in out and '<line' in out and 'text-anchor="start"' in out


def test_tikz():
    s, *_ = small()
    t = s.to_tikz()
    assert t.startswith('% t') and '\\begin{tikzpicture}' in t and '\\end{tikzpicture}' in t
    assert '$\\Omega$' in t and '\\textsubscript{1}' in t and '\\overline' in t and '\\itshape' in t
    full = EX.export(s.doc, 'tikz-standalone')[0].decode()
    assert full.startswith('\\documentclass[tikz')


# ---------------------------------------------------------------- SPICE simulation decks
def test_directives_and_default_models():
    s = Schematic('sim')
    v = s.vsrc((0, 0), rot=90, value='SIN(0 1 1k)')
    d = s.diode(anchor='A', at=v['p'])
    u = s.opamp((200, 0))
    s.directive('.tran 1u 1m', '.ac dec 10 10 1Meg')
    sp = s.spice()
    assert '.model DMOD D(' in sp and '.subckt OPAMP inp inm out' in sp
    assert sp.index('.tran 1u 1m') > sp.index('.model DMOD') and '.save all' in sp and sp.rstrip().endswith('.end')
    s.directive('.model DMOD D(Is=1n)')
    assert s.spice().count('.model DMOD') == 1                    # a user model replaces the default
    back = Schematic.from_netlist(sp, 'spice')
    assert back.doc['spice'] == ['.tran 1u 1m', '.ac dec 10 10 1Meg', '.save all']
    assert d and u


def test_simulation_runs(tmp_path):
    if not shutil.which('ngspice'):
        pytest.skip('ngspice not installed')
    s = Schematic('rc')
    v = s.vsrc((0, 0), rot=90, kind='pulse', value='PULSE(0 1 0.5m 1n 1n 10m 20m)')
    s.gnd(v['n'])
    r = s.resistor(anchor='1', at=v['p'], value='1k')
    c = s.capacitor(anchor='1', at=r['2'], rot=90, value='1u')
    s.gnd(c['2'])
    s.flag(r['2'], 'OUT')
    s.directive('.tran 5u 3m', '.meas tran vtau FIND v(OUT) AT=1.5m')
    deck = tmp_path / 'rc.cir'
    deck.write_text(s.spice())
    out = subprocess.run(['ngspice', '-b', str(deck)], capture_output=True, text=True, timeout=60).stdout
    v1 = float(out.split('vtau')[1].split('=')[1].split()[0])
    assert abs(v1 - 0.632) < 0.01


# ---------------------------------------------------------------- examples and legacy scripts
def test_legacy_script_runs_as_a_script():
    code = open(os.path.join(HERE, '..', 'schematrix', 'examples', 'tr-0002', 'schematics.py')).read()
    res = runner.run(code, 'script', 'schematics.py', 120)
    assert res['ok'] and len(res['docs']) == 12


def test_examples_run():
    ex = os.path.join(HERE, '..', 'schematrix', 'examples')
    scripts = [os.path.join(dp, f) for dp, _, fs in os.walk(ex) for f in fs if f.endswith('.py') and 'tr-0002' not in dp]
    assert len(scripts) >= 20
    for path in scripts:
        res = runner.run(open(path).read(), 'script', path, 120, cwd=os.path.dirname(path))
        assert res['ok'], (path, res.get('traceback'))
        assert res['docs'], path


def test_workspace_seeding_adds_new_examples_once(tmp_path, monkeypatch):
    from schematrix import server
    ws = tmp_path / 'ws'
    monkeypatch.setenv('SCHEMATRIX_WORKSPACE', str(ws))
    server.workspace()
    f = ws / 'examples' / 'analog' / 'inverting-amplifier.py'
    assert f.exists()
    f.unlink()
    server.workspace()
    assert not f.exists()                                  # deleted on purpose: not brought back
    assert netio.detect(open(ws / 'examples' / 'netlists' / 'linear-supply.net').read()) == 'kicad'


def test_cairo_text_is_drawn_from_the_bundled_fonts():
    """PDF / PNG must not depend on the computer's fonts: bundled-font text becomes outlines, other text stays"""
    pytest.importorskip('fontTools')
    pytest.importorskip('brotli')
    from schematrix import Schematic
    from schematrix.outline import outline
    s = Schematic('t')
    s.text(0, 20, 'I− e₍ₙ₎ √ → ~{RST} V_{OUT}', 'lbl'); s.text(0, 40, 'note eₙ', 'note')
    out = outline(s.to_svg())
    assert '<text' not in out and out.count('class="txt"') == 2
    assert 'stroke-width' in out.split('class="txt"')[1]                        # the overbar
    formal = Schematic('f', theme='formal'); formal.text(0, 20, 'Times', 'lbl')
    assert '<text' not in outline(formal.to_svg())                                # TeX Gyre Termes ships too
    kicad = Schematic('k', theme='kicad'); kicad.text(0, 20, 'KiCad', 'lbl')
    assert '<text' in outline(kicad.to_svg())                                     # system fonts: left as text
