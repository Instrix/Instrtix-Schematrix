# Schematrix

An electrical schematic editor in the Instrix house style (the look of the TR-0002 figures), with a Python
scripting library behind it. The same core renders, netlists and serves the GUI, so a schematic drawn by hand and
one built by a script are the same kind of document.

![Editor](docs/editor.png)

- **GUI**: browser-based editor — symbol palette, wires that snap to pins and follow parts when moved, net labels,
  group boxes, notes, undo/redo, tabs, themes, netlist view, and a Python script pane.
- **Scripting**: `from schematrix import Schematic` — place parts, reach pins as `part['pin']`, route wires,
  save JSON / SVG / PNG / PDF / SPICE. Scripts run from the editor, the CLI, or plain Python / Jupyter.
- **Legacy import**: figure scripts written against the old hand-rolled `S` class (like `schematics.py`) run
  unchanged and come out as editable documents, pixel-identical to the originals.
- **Runs** as a Docker web app, or natively on Windows and Linux (own window via pywebview).

## Quick start

```bash
pip install -e ".[export,desktop]"     # export = PNG/PDF, desktop = native window
schematrix                               # native window (falls back to the browser)
schematrix serve --open                  # web server on http://127.0.0.1:8000
```

The workspace (default `~/Schematrix`, `/data` in Docker) holds saved `.json` schematics and `.py` scripts. On first
run it is seeded with `examples/`: the twelve TR-0002 figures and a sample script.

### Docker

```bash
docker compose up -d                   # http://localhost:8000, data in the schematrix-data volume
```

| Variable | Default | |
|---|---|---|
| `SCHEMATRIX_WORKSPACE` | `~/Schematrix` (`/data` in Docker) | documents and scripts |
| `SCHEMATRIX_SCRIPTS` | `1` | allow the editor to run Python on the server |
| `SCHEMATRIX_TOKEN` | unset | if set, every request needs it: open `/?token=…` once (sets a cookie) or send `Authorization: Bearer …` |
| `SCHEMATRIX_SCRIPT_TIMEOUT` | `30` | seconds per script |

Scripts are arbitrary Python running on the server (in a child process with a timeout and, on Linux, memory/CPU
limits). On anything shared, set `SCHEMATRIX_TOKEN` or `SCHEMATRIX_SCRIPTS=0`.

### Native builds (Windows / Linux)

```bash
pip install ".[desktop]" pyinstaller
pyinstaller packaging/schematrix.spec    # -> dist/Schematrix/Schematrix(.exe)
```

The CI workflow (`.github/workflows/release.yml`) runs the tests, builds both native bundles and pushes the Docker
image on a `v*` tag. Windows uses WebView2 (preinstalled on Windows 10/11); Linux needs GTK WebKit
(`gir1.2-webkit2-4.1`) for the native window, otherwise it opens the browser.

## Scripting

```python
from schematrix import Schematic

s = Schematic('RC filter and buffer')
vin = s.flag((60, 120), 'VIN', side='left')
r1 = s.resistor((130, 120), value='1 kΩ')                         # ref R1 assigned automatically
c1 = s.capacitor(anchor='1', at=(200, 120), rot=90, value='10 nF')  # put pin 1 at (200, 120)
s.gnd(c1['2'])
u1 = s.opamp(anchor='inp', at=(280, 120), top='+', part='OPA210')
s.wire(vin['p'], r1['1'])
s.wire(r1['2'], u1['inp'])                                         # junction dots are automatic
s.route(u1['out'], (380, 160), how='hv', style='acc')              # orthogonal routing; 'acc' = accent blue
s.note(60, 230, 'f_c ≈ 15.9 kHz')

s.save('rc.json'); s.save_svg('rc.svg'); s.save_pdf('rc.pdf')
print(s.spice())
```

- Every symbol is a method: `s.resistor`, `s.nmos`, `s.opamp`, `s.vsrc`, `s.gate(kind='nand', inputs=3)`,
  `s.block(w=, h=, title=, pins='IN:l, OUT:r')`, … — `schematrix symbols` lists them with their pins and properties.
- Placement: `at`, `rot` (0/90/180/270), `mirror`, `anchor=<pin>`; `style` = `''`, `'acc'`, `'para'` (dashed).
- Annotation: `text`, `note`, `heading`, `rect` (group shading), `group([parts], label=)`, `arrow`, `raw(svg)`.
- Page: `Schematic(title, width, height, theme=…)`, `.page(...)`, `.fit()`; themes `instrix`, `instrix-dark`,
  `blueprint`, `print-mono`, or a dict of token overrides.
- In the editor, every schematic a script creates (or passes to `show()`) opens as a tab.

## CLI

```
schematrix render fig.json -o fig.svg            # or .png / .pdf / .cir; --fonts embeds fonts in the SVG
schematrix render build_figs.py -o out/ -f svg,pdf
schematrix netlist fig.json
schematrix import-legacy schematics.py -o figs/  # old S-class scripts -> .json + .svg
schematrix symbols
```

## Layout

```
schematrix/
  symbols.py    symbol library: geometry, pins, label blocks (single source of truth, served to the editor)
  geometry.py   placement maths, junctions, bounding boxes   (web/js/geom.js is its JS twin)
  render.py     document -> SVG (and PNG/PDF via cairosvg)
  document.py   the scripting API (Schematic, Comp, Pin)
  netlist.py    connectivity and SPICE
  compat.py     legacy S-class importer
  runner.py     sandboxed script execution
  server.py     FastAPI: /api/symbols, /geometry, /render, /netlist, /run, /files …  (docs at /api/docs)
  cli.py        command line + native launcher
  web/          the editor (vanilla JS modules, no build step) and the bundled JetBrains Mono / Inter fonts
```

Adding a symbol is one decorated function in `symbols.py` returning primitives and pins; the editor picks it up
from `/api/symbols` with no front-end change.

## Document format

```json
{"version": 1, "meta": {"title": "", "description": ""},
 "page": {"width": 800, "height": 500, "auto": false, "margin": 20, "grid": 5, "junctions": true},
 "theme": "instrix",
 "elements": [
   {"id": "e1", "type": "comp", "sym": "resistor", "x": 100, "y": 100, "rot": 0, "mirror": false,
    "props": {"ref": "R1", "value": "1 kΩ"}, "style": ""},
   {"id": "e2", "type": "wire", "points": [[130, 100], [200, 100]], "style": "acc"},
   {"id": "e3", "type": "text", "x": 60, "y": 230, "text": "note", "cls": "note", "anchor": "start"}]}
```

Element types: `comp`, `wire`, `arrow`, `text`, `rect`, `raw`. Element order is drawing order.

Fonts: JetBrains Mono and Inter (SIL OFL 1.1, licences in `web/fonts/`).
