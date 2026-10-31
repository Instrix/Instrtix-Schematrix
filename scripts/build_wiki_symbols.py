"""Regenerate docs/wiki/Symbol-Library.md and its symbol pictures from the live symbol library.

    python scripts/build_wiki_symbols.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from schematrix import render as R  # noqa: E402
from schematrix import symbols as SYM  # noqa: E402

WIKI = ROOT / 'docs' / 'wiki'
IMG = WIKI / 'img' / 'symbols'


def picture(name, props, file):
    doc = {'elements': [{'id': 'p', 'type': 'comp', 'sym': name, 'x': 0, 'y': 0, 'props': props, 'hide_labels': True}],
           'page': {'auto': True, 'margin': 6, 'junctions': False}, 'theme': 'instrix'}
    (IMG / file).write_text(R.render_svg(doc), encoding='utf-8')


def cell(s):
    return str(s).replace('|', '\\|').replace('\n', ' ')


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    for f in IMG.glob('*.svg'):
        f.unlink()
    out = ['# Symbol library', '',
           'Every built-in symbol, generated from the library itself (`python scripts/build_wiki_symbols.py`).',
           'In Python each symbol is a method of `Schematic` (`s.resistor(...)`), and so is each named variant',
           '(`s.zener(...)`). Settings marked *shape* change the drawing; the others are information.', '',
           'Every part also has **Reference**, **Value** and **Part number**, and can carry any number of',
           '[fields](Fields-and-Properties.md). Pins are named as listed; the netlist uses these names.', '']
    cats = {}
    for e in SYM.catalog():
        if e.get('custom'):
            continue
        cats.setdefault(e['category'], []).append(e)
    out.append('**Categories:** ' + ' · '.join(f'[{c}](#{re.sub(r"[^a-z0-9 -]", "", c.lower()).replace(" ", "-")})' for c in cats))
    out.append('')
    for cat, entries in cats.items():
        out += [f'## {cat}', '']
        for e in entries:
            name = e['name']
            picture(name, {}, f'{name}.svg')
            props = [(k, p) for k, p in e['props'].items() if k not in ('ref', 'value', 'part')]
            out += [f'### {e["title"]}', '',
                    f'<img src="img/symbols/{name}.svg" alt="{e["title"]}" height="70">', '',
                    f'- **Python:** `s.{name}(...)`  ·  **Reference prefix:** `{e["prefix"] or "—"}`'
                    + (f'  ·  **SPICE:** `{e["spice_template"]}`' if e.get('spice_template') else ''),
                    '- **Pins:** ' + ', '.join(f'`{p}`' for p in e['geometry']['pins'])]
            if e.get('help'):
                out.append(f'- {e["help"]}')
            if e.get('fields'):
                out.append('- **Suggested fields:** ' + ', '.join(e['fields']))
            if props:
                out += ['', '| Setting | Type | Default | |', '|---|---|---|---|']
                for k, p in props:
                    typ = p['type'] + (': ' + ', '.join(str(c) for c in p['choices']) if p.get('choices') else '')
                    out.append(f'| `{k}` ({cell(p["label"])}) | {cell(typ)} | `{cell(p["default"])}` | '
                               f'{"*shape*" if p["geom"] else ""} {cell(p.get("help", ""))} |')
            if e['presets']:
                out += ['', '**Named variants** (each has its own palette tile and Python method):', '',
                        '| | Variant | Python | Same as |', '|---|---|---|---|']
                for pr in e['presets']:
                    picture(name, pr['props'], f'{pr["name"]}.svg')
                    same = ', '.join(f'{k}={v!r}' for k, v in pr['props'].items()) or 'the defaults'
                    out.append(f'| <img src="img/symbols/{pr["name"]}.svg" height="48"> | {pr["title"]} | '
                               f'`s.{pr["name"]}()` | `{name}` with {same} |')
            out.append('')
    (WIKI / 'Symbol-Library.md').write_text('\n'.join(out) + '\n', encoding='utf-8')
    print('wrote', WIKI / 'Symbol-Library.md', len(list(IMG.glob('*.svg'))), 'pictures')


if __name__ == '__main__':
    main()
