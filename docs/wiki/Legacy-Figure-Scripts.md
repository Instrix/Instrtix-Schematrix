# Legacy figure scripts

Before Schematrix, the TR-0002 figures were drawn by Python scripts built on a hand-rolled `S` class that wrote SVG
directly (`examples/tr-0002/schematics.py`). Schematrix reads those scripts and turns every figure into an editable
document, pixel-identical to the original SVG (a test checks this).

## Importing

Any of these works; a script that defines `class S` with an `svg()` method is recognised automatically:

- **Editor**: open the script (File > Open from workspace, Open file from computer, or drag it in) and run it in the
  Script pane, or *File > Import legacy figure script…*. Each figure opens as a tab.
- **Command line**: `schematrix import-legacy schematics.py -o figs/ -f json,svg`, or `schematrix render
  schematics.py -o figs/ -f json`.
- **Python**: `from schematrix.compat import import_legacy; for name, sch in import_legacy('schematics.py'): ...`

Run with plain Python (`python schematics.py`), the script still writes its SVGs into its
`tr-0002-afe1-10-analog-front-end/` folder as it always did.

## What comes out

The importer replays the script with a compatible `S` class that records what each call draws: resistors,
capacitors, op-amps, MOSFETs, switches, grounds, wires, texts, blocks and boxes become real Schematrix elements (so
they can be moved, restyled, netlisted and exported); markup the old class wrote directly is kept as `raw` SVG elements
that render exactly as before. Junction dots are left as the script drew them.
