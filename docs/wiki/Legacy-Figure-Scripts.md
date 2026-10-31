# Legacy figure scripts

Before Schematrix, the figures in the Instrix documentation were drawn by Python scripts built on a hand-rolled `S` class that wrote SVG
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
capacitors, op-amps, MOSFETs, switches, sources, grounds, wires, texts, blocks and boxes become real Schematrix
elements (so they can be moved, restyled, netlisted and exported). The documents use the original figures' line
widths for flags, pads and terminals (`lw_flag` 1.2, `lw_pad` 1.4, `lw_term` 1.8).

Markup written directly with `s.add(...)` also becomes real elements when it is one of these shapes:

| Raw markup | Becomes |
|---|---|
| `<rect class="grp / box / pad / accbox" …>` (`style="fill:#dbe8f3"` = accent box) | a rectangle |
| `<line class="w" … stroke-dasharray="2 4">` | a dashed `rule` line |
| `<polygon class="arrow / accf">` at the end of a wire | that wire becomes an arrow with the same head size |
| `<polygon class="amp">` square triangle | a buffer; an `r = 4` pad circle at its tip makes it inverting |
| `<polygon class="amp">` 13 × 14 triangle followed by its bar | a diode |
| `<polygon class="arrow">` part-way along a wire | a direction mark on that wire (it stays connected) |
| `<circle class="amp" r="16">` with a label centred in it | a voltage source with that text (e.g. `eₙ`) |
| `<circle class="amp" r="16">` with an arrow inside | a current source with that same arrow |

Anything else stays a raw element that renders exactly as before. The bundled example converts completely (no raw
markup left), and 11 of its 12 figures are pixel-identical to the originals; the twelfth differs where the old script
drew one resistor bottom-to-top and garbled its zigzag. Junction dots are left as the script drew them.

Scripts written or edited for Schematrix can call these directly on `S`:

```python
s.rect(x, y, w, h, cls='grp', rx=3, label='STAGE 1')     # label: group caption at the top left
s.arrow((x1, y1), (x2, y2), cls='w', head=(11, 4))        # cls 'w acc' for the accent colour
s.buffer(x, y, size=22, invert=True)                      # base centred on (x, y), pointing right
s.diode(x1, y1, x2, y2, kind='schottky')                  # anode -> cathode, any diode kind
```

`import_legacy(path, embed_fonts=True)` (or `--fonts` on the command line) embeds the fonts in the SVGs, so
characters like `−`, `√`, `→` and `eₙ` show everywhere, not only where JetBrains Mono is installed.
