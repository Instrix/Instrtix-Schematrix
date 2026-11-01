"""markup.py and web/js/markup.js must parse every label the same way (the editor and the exports draw from them)."""
import json
import os
import shutil
import subprocess

import pytest

from schematrix import markup as MU

HERE = os.path.dirname(os.path.abspath(__file__))
JS = os.path.join(HERE, '..', 'schematrix', 'web', 'js', 'markup.js')
CASES = [
    'plain', '~{RST}', 'V_{CC}', 'x^{2}', '~{CS_{1}}', '10 k\\ohm', '25 \\deg{}C', '\\pm1 %', 'f_c', 'a\\_b', '\\-5 V',
    r'$V_{out} = \frac{R_2}{R_1} V_{in}$', r'$f_c = \frac{1}{2\pi R C}$', r'gain $A_v = -\frac{R_f}{R_{in}}$ (inv.)',
    r'cost \$5', '$5 only', r'$\Delta V \approx 10\,\mathrm{mV}$', r'$\sqrt{2} \cdot \pi$', r'$a+b-c$',
    r'$x \text{ if } y$', r'$I_{DS} = \frac{1}{2}\mu C_{ox}\frac{W}{L}(V_{GS}-V_{th})^2$', r'$\overline{Q}$ and ~{Q}',
]


def py(s):
    return [[t, sorted(f)] for t, f in MU.parse(s)]


@pytest.mark.skipif(not shutil.which('node'), reason='needs node')
def test_python_and_js_markup_agree(tmp_path):
    script = tmp_path / 't.mjs'
    script.write_text(f"import {{ parse }} from {json.dumps('file://' + os.path.abspath(JS))};\n"
                      f"const cases = {json.dumps(CASES)};\n"
                      "console.log(JSON.stringify(cases.map((s) => parse(s).map(([t, f]) => [t, [...f].sort()]))));\n")
    js = json.loads(subprocess.run(['node', str(script)], capture_output=True, text=True, check=True).stdout)
    for s, a, b in zip(CASES, [py(s) for s in CASES], js):
        assert a == b, s


def test_math():
    assert MU.plain(r'$V_{out} = \frac{R_2}{R_1} V_{in}$') == 'Vout = R2/R1 Vin'
    assert MU.plain(r'$f_c = \frac{1}{2\pi R C}$') == 'fc = 1/(2πRC)'
    assert MU.plain(r'cost \$5') == 'cost $5' and MU.plain('$5 only') == '$5 only'
    assert MU.to_latex(r'gain $A_v = -\frac{R_f}{R_{in}}$ V_{x}', lambda s: s) == \
        r'gain $A_v = -\frac{R_f}{R_{in}}$ V\textsubscript{x}'


def test_tikz_gets_the_latex_maths():
    from schematrix import Schematic
    s = Schematic()
    s.text(0, 0, r'$A_v = -\frac{R_f}{R_{in}}$', 'lbl')
    assert r'{$A_v = -\frac{R_f}{R_{in}}$}' in s.to_tikz()
