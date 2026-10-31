"""Regenerate the example documents and sample netlists from the example scripts.

    python scripts/build_examples.py

Each examples/<folder>/<name>.py is run; every schematic it shows is saved next to it as <title>.json (so the
editor's file dialog opens it directly). examples/netlists/ gets SPICE / KiCad / JSON netlists of a few of them.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from schematrix import netio, runner  # noqa: E402

EX = ROOT / 'schematrix' / 'examples'
slug = lambda s: re.sub(r'[^\w\-]+', '-', s.lower()).strip('-')
NETLISTS = {'analog/inverting-amplifier.py': 'spice', 'simulation/rlc-resonance.py': 'spice',
            'power/linear-supply.py': 'kicad', 'digital/full-adder.py': 'json', 'analog/common-emitter.py': 'kicad'}


def main():
    out = EX / 'netlists'
    out.mkdir(exist_ok=True)
    for script in sorted(EX.glob('*/*.py')):
        if script.parent.name == 'tr-0002':
            continue
        res = runner.run(script.read_text(), 'script', script.name, 120, cwd=str(script.parent))
        if not res['ok']:
            sys.exit(f'{script}: {res.get("traceback") or res.get("error")}')
        for d in res['docs']:
            path = script.parent / f'{slug(d["name"])}.json'
            path.write_text(json.dumps(d['doc'], indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
            print('wrote', path.relative_to(ROOT))
        rel = script.relative_to(EX).as_posix()
        if rel in NETLISTS and res['docs']:
            fmt = NETLISTS[rel]
            path = out / f'{script.stem}{netio.EXT[fmt]}'
            path.write_text(netio.export(res['docs'][0]['doc'], fmt), encoding='utf-8')
            print('wrote', path.relative_to(ROOT))


if __name__ == '__main__':
    main()
