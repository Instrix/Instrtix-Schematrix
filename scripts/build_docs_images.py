"""Render the documentation images that show drawings: one sample circuit in every theme, plus export samples.

    python scripts/build_docs_images.py            # needs playwright and a Chromium (pip install playwright)

Writes docs/wiki/img/themes/<theme>.png and docs/wiki/img/sample.svg. The editor screenshots are taken by hand
(see Development.md).
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from schematrix import Schematic, theme as TH  # noqa: E402

OUT = ROOT / 'docs' / 'wiki' / 'img'


def sample(theme):
    s = Schematic(f'{theme}', theme=theme)
    u = s.opamp((300, 110), top='-', ref='U1', part='OPA210')
    r1 = s.resistor(anchor='2', at=(230, 95), value='10 k\\ohm', ref='R1', fields={'Tolerance': ('\\pm1 %', True)})
    s.wire(r1['2'], u['inm'])
    s.wire((250, 95), (250, 30), (270, 30))
    r2 = s.resistor(anchor='1', at=(270, 30), value='100 k\\ohm', ref='R2')
    s.wire(r2['2'], (360, 30), (360, 110))
    s.gnd(s.wire(u['inp'], (250, 125), (250, 145))[-1])
    s.flag(s.wire(r1['1'], (130, 95))[-1], 'V_{IN}', side='left')
    s.flag(s.wire(u['out'], (400, 110))[-1], 'V_{OUT}', side='right')
    c = s.capacitor(anchor='1', at=(160, 95), rot=90, value='1 nF', ref='C1')
    s.gnd(c['2'])
    ff = s.dff((760, 80), ref='U3')
    g = s.nand_gate(anchor='out', at=(ff['D'][0] - 30, ff['D'][1]), ref='U2')
    s.wire(g['out'], ff['D'])
    s.flag(s.wire(g['in1'], (g['in1'][0] - 30, g['in1'][1]))[-1], '~{EN}', side='left', min_width=50)
    s.flag(s.wire(g['in2'], (g['in2'][0] - 30, g['in2'][1]))[-1], 'DATA', side='left', min_width=50)
    c = ff['CLK']
    s.flag(s.wire(c, (c[0] - 15, c[1]), (c[0] - 15, c[1] + 40), (g['in2'][0] - 30, c[1] + 40))[-1], 'CLK', side='left', min_width=50)
    s.flag(s.wire(ff['Q'], (ff['Q'][0] + 30, ff['Q'][1]))[-1], 'Q', side='right')
    s.flag(s.wire(ff['QN'], (ff['QN'][0] + 30, ff['QN'][1]))[-1], '~{Q}', side='right')
    s.heading(130, 0, f'{theme}')
    s.note(130, 200, 'A_{v} = \\-R2 / R1 = \\-10,   f_{c} \\approx 16 kHz')
    return s


def main():
    from playwright.sync_api import sync_playwright
    (OUT / 'themes').mkdir(parents=True, exist_ok=True)
    chrome = shutil.which('chromium') or shutil.which('google-chrome') or shutil.which('chromium-browser')
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=chrome) if chrome else p.chromium.launch()
        pg = b.new_page(device_scale_factor=2)
        for name in TH.THEMES:
            svg = sample(name).to_svg(embed_fonts=True)
            pg.set_content(f'<body style="margin:0">{svg}</body>')
            pg.locator('svg').screenshot(path=str(OUT / 'themes' / f'{name}.png'))
            print('wrote', name)
        b.close()
    (OUT / 'sample.svg').write_text(sample('instrix').to_svg(embed_fonts=False), encoding='utf-8')


if __name__ == '__main__':
    main()
