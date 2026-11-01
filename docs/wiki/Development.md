# Development

## Setup

```bash
git clone git@github.com:Instrix/instrtix-schematrix.git && cd instrtix-schematrix
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,desktop]"
pytest -q                     # ~140 tests, a few seconds
schematrix serve --open       # the editor against your working copy (reload the page after JS changes)
```

## Code layout

```
schematrix/
  symbols/        the symbol library (single source of truth, served to the editor)
    core.py         Prop, Symbol, the @symbol registry and presets, primitives and drawing helpers
    passive.py semiconductor.py analog.py logic.py digital.py sources.py loads.py electromech.py
    tubes.py signal.py generic.py nets.py        one module per palette category
    logic_block.py  the engine behind registers, counters, decoders and custom logic ICs
    custom.py       user-drawn symbols (JSON definitions)
  geometry.py     placement maths, label blocks, junctions, hops, bounding boxes   (twin: web/js/geom.js)
  markup.py       text markup                                                        (twin: web/js/markup.js)
  render.py       document -> SVG
  export.py       every export format, selection cropping, backgrounds; cairo fixes
  tikz.py         SVG -> TikZ
  theme.py        themes and the drawing CSS
  frame.py        page frames and title blocks
  document.py     the scripting API (Schematic, Comp, Pin)
  netlist.py      connectivity: nets, names, buses
  netio/          netlist files: model.py, spice.py, kicad.py, jsonfmt.py, layout.py
  units.py        engineering values
  compat.py       legacy S-class importer
  runner.py       sandboxed script execution
  server.py       FastAPI app;  public.py: public-mode limits and hardening
  cli.py          command line and app launcher
  web/            the editor: vanilla ES modules, no build step
    js/app.js       entry point; state, view, tools, selection, inspector, palette, panes, files, ui, commands,
                    exporter, find, symedit, util modules
  examples/       bundled examples (seeded into workspaces)
deploy/           Docker Compose templates;  packaging/  PyInstaller spec, installers, icons;  scripts/  generators
```

**Twins**: `geometry.py` / `geom.js` and `markup.py` / `markup.js` must stay in step (the server renders exports, the
browser renders the editor). Tests compare the markup twins; check geometry changes in both.

## Adding a symbol

Write a function in the fitting `symbols/` module and decorate it:

```python
@symbol('ptc_fuse', 'PTC fuse', 'Passive', 'F', 'R {1} {2} 10m',
        {'length': LEN(60)},
        fields=('Hold current', 'Trip current'),
        aliases=('Polyfuse',),                       # KiCad library names for import
        pin_numbers={'1': '1', '2': '2'},            # KiCad numbering, if not 1..n
        presets=(('resettable_fuse', 'Resettable fuse', {}, ('Fuse_Polyfuse',)),))
def ptc_fuse(p):
    h = half(p)
    return G([*leads(h, 12), iec_box(12), pl([(-16, 10), (-10, 10), (10, -10)])], two_pins(h), above(-12))
```

It appears in the palette, the Python API, netlists and the importers with no other change. Conventions: pins on
the 5-unit grid; two-terminal parts along +x with pin 1 on the left; `tx(..., fit=width)` for user text inside a body.
Run `python scripts/build_wiki_symbols.py` to refresh the [Symbol library](Symbol-Library.md) page.

## Generators

| Script | Writes |
|---|---|
| `scripts/build_examples.py` | the examples' `.json` documents and sample netlists |
| `scripts/build_wiki_symbols.py` | `docs/wiki/Symbol-Library.md` and its symbol pictures |
| `scripts/build_docs_images.py` | the theme gallery images (needs Playwright + Chromium) |

Editor screenshots in `docs/wiki/img/` are taken with Playwright against a running server.

## Tests

`tests/` covers the core and geometry, netlists (round trips, foreign SPICE / KiCad), buses, symbols and presets,
custom symbols and frames, exports (every format, markup, TikZ, cairo fixes), simulation (runs ngspice when installed),
the examples, the server (private and public mode) and the legacy importer (pixel comparison, needs cairosvg).

## Releases

1. Bump the version in `pyproject.toml` and `schematrix/__init__.py`.
2. Tag: `git tag v0.2.6 && git push --tags`.
3. `release.yml` tests (and checks the tag matches the version), then builds:
   - Linux (Ubuntu 22.04, so glibc 2.35 and newer): `Schematrix-x86_64.AppImage`, `schematrix_amd64.deb`;
   - Windows: `Schematrix-Setup.exe` (Inno Setup, per-user or all users), `Schematrix-windows.zip` (portable);
   - macOS (Apple silicon): `Schematrix-macos.dmg` (unsigned);
   - the wheel and source archive, and the Docker image `ghcr.io/instrix/instrtix-schematrix:<tag>` and `:latest`;

   and publishes them as the GitHub release for the tag, with generated notes. The file names carry no version, so
   `releases/latest/download/<name>` always points at the newest. Started by hand from the Actions tab, or by pushing
   a `build/<anything>` branch, it builds everything as run artifacts without releasing. Every native build first
   exports a PDF and a PNG with the packaged app itself (the Windows and macOS apps carry their own Cairo).

Other workflows: `ci.yml` runs the tests on Python 3.10 and 3.12 for every push and pull request; `pages.yml`
publishes `docs/` (this wiki) to GitHub Pages when it changes. Packaging lives in `packaging/`: `schematrix.spec`
(PyInstaller), `package.py` (installers), `schematrix.iss` (Inno Setup), `launcher.py` and the icons (`icon.svg`
is the source).

### PyPI

On a version tag the `pypi` job uploads the wheel and source archive to [PyPI](https://pypi.org/project/schematrix/)
with trusted publishing (no token stored anywhere). It needs a one-time setup on pypi.org, under *Your account >
Publishing > Add a new pending publisher*: project `schematrix`, owner `Instrix`, repository `Instrtix-Schematrix`,
workflow `release.yml`, environment `pypi`. The build rewrites the README's relative links to absolute ones at the
tag (`packaging/pypi_readme.py`) so its pictures show on PyPI. A failed upload does not stop the GitHub release.

Commit messages: plain, no co-author or tool trailers.
