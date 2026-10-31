# Getting started

This walk-through draws an RC low-pass filter, names its nets, exports it, and then builds the same circuit in
Python. It takes about ten minutes. Install first ([Installation](Installation.md)) and run `schematrix`.

## 1. Place parts

The **palette** on the left lists every symbol by category; type in **Find a symbol…** (or press `/`) to filter.

- **Drag** a tile onto the sheet to place one part, or
- **click** a tile, then click on the sheet as often as you like (Esc stops placing).

While placing, `R` rotates and `M` mirrors the part under the cursor.

Place a **Voltage source**, a **Resistor**, a **Capacitor** and a **Ground**. References (V1, R1, C1) are numbered
automatically.

## 2. Wire them

Press `W` (or the **Wire** tool). Click to start, click to add corners, and finish on a pin: wires snap to pins,
to other wires' ends and to the middle of wires. The elbow follows your mouse; `/` flips it. `Enter`, `Esc` or a
right-click ends a wire anywhere.

Where three or more connections meet, a **junction dot** appears by itself.

## 3. Edit values

Click a part to select it; the **Properties** pane on the right shows its settings. Type `1 k\ohm` as the resistor
value (the `\ohm` becomes Ω, see [Text markup](Text-Markup.md)) and `10 nF` for the capacitor. Or double-click the
value on the sheet to edit it in place.

## 4. Name the output

Press `L` (**Label**) and click the wire between R1 and C1; type `OUT`. Net labels name nets for the netlist and join
every wire that carries the same name, even across the sheet.

## 5. Save and export

- **Save** (`Ctrl S`) stores the sheet in your workspace (`~/Schematrix` by default). Everything is also autosaved in
  the browser while you work.
- **Export** (`Ctrl E`): pick a format (SVG, PNG, PDF, TikZ, …), the area (whole sheet or the selection), the
  background and the resolution. See [Exporting](Exporting.md).

## 6. Check the netlist

Open the **Netlist** tab on the right and press **Extract netlist**: nets, their pins and any warnings (unconnected
pins, …). **Download** writes SPICE, KiCad or JSON. See [Netlists](Netlists.md).

## 7. The same circuit in Python

Open the **Script** tab, paste this and press `Ctrl Enter`:

```python
from schematrix import Schematic

s = Schematic('RC low-pass')
v = s.vsrc((60, 160), rot=90, kind='ac', value='AC 1')
s.gnd(v['n'])
r = s.resistor(anchor='1', at=(60, 100), value='1 k\\ohm')
s.wire(v['p'], r['1'])
c = s.capacitor(anchor='1', at=r['2'], rot=90, value='10 nF')
s.gnd(c['2'])
s.flag(s.wire(r['2'], (160, 100))[-1], 'OUT', side='right')
s.directive('.ac dec 20 10 1Meg')
s.show()
```

The schematic opens as a new tab, ready to edit by hand. The same script runs outside the editor:
`schematrix render rc.py -f svg,pdf` or `python rc.py` (add `s.save('rc.json')`). See
[Python scripting](Python-Scripting.md).

## Where next

- More drawing tools: [The editor](Editor.md) and [Keyboard and mouse](Keyboard-and-Mouse.md)
- Every symbol: [Symbol library](Symbol-Library.md)
- Figures for a paper: [Using Schematrix in LaTeX](LaTeX.md)
- Ready-made sheets to learn from: [Examples](Examples.md)
