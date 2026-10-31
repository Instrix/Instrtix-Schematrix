# Python scripting

Everything the editor draws can be built from Python. Scripts run in the editor's Script pane, from the
[command line](Command-Line.md) (`schematrix render script.py`), or as plain Python / Jupyter after
`pip install schematrix` ([Installation](Installation.md)).

```python
from schematrix import Schematic

s = Schematic('RC filter and buffer', description='First-order low-pass into a follower')
vin = s.flag((60, 120), 'V_{IN}', side='left')
r1 = s.resistor((130, 120), value='1 k\\ohm')                         # ref R1 assigned automatically
c1 = s.capacitor(anchor='1', at=(200, 120), rot=90, value='10 nF')  # put pin 1 of C1 at (200, 120)
s.gnd(c1['2'])
u1 = s.opamp(anchor='inp', at=(280, 120), top='+', part='OPA210')
s.wire(vin['p'], r1['1'])
s.wire(r1['2'], u1['inp'])                                         # junction dots are automatic
s.route(u1['out'], (380, 160), how='hv', style='acc')
s.note(60, 230, 'f_{c} \\approx 15.9 kHz')

s.save('rc.json')                 # open it in the editor
s.export('rc.pdf')                # or .svg .png .tikz …
print(s.spice())
```

In a Python string, write markup backslashes twice (`'1 k\\ohm'`) or use raw strings (`r'1 k\ohm'`).

## Coordinates

Drawing units are CSS pixels (96 per inch); y grows downwards. Parts are drawn on a 5-unit grid; keep pins on it.
Rotation is clockwise in 90° steps; `mirror=True` flips left-right before rotating.

## The Schematic

```python
s = Schematic(title='', width=None, height=None, *, theme='instrix', grid=5, description='',
              junctions=True, hops=False, margin=20)
```

Without `width` / `height` the page is sized to the drawing (+ `margin`).

| Method | |
|---|---|
| `s.page(width=, height=, auto=, margin=, grid=, junctions=, hops=, theme=, description=)` | change page settings |
| `s.fit(margin=20)` | fix the page to the current drawing |
| `s.frame('A4', 'landscape', title=…, rev=…)` | [page frame](Page-Frames.md); `s.frame(None)` removes it |
| `s.title` | the title (read / write) |

## Placing parts

Every symbol and [variant](Symbol-Library.md) is a method:

```python
r = s.resistor(at=(100, 50), rot=0, mirror=False, ref=None, value=None, part=None,
               style='', label_offset=None, hide_labels=False, fields=None, **settings)
z = s.zener((200, 50), value='5V1')                  # a variant: diode with kind='zener'
g = s.nand_gate((300, 50), inputs=3, shape='iec')
u = s.add('opamp', (400, 50), top='+')               # by name
```

- `anchor='pin'` places the part so that pin lands on `at`: `s.capacitor(anchor='1', at=r['2'], rot=90)`.
- `ref` is assigned from the symbol's prefix when omitted (R1, R2, …).
- Symbol settings are keywords (`kind='schottky'`, `bits=8`, `bus=True`, `length=40`); unknown ones raise an error
  that lists the valid ones.
- `fields={'Tolerance': ('1%', True), 'Power': '0.25 W'}` ([fields](Fields-and-Properties.md)).
- `style='acc'` / `'para'` / `'acc para'` ([styles](Styles-and-Themes.md#line-styles)).

Net symbols take their name positionally:

```python
s.flag(at, 'CLK', side='right')     # net label (side: which way the flag points)
s.rail(at, '+5 V', kind='bar')      # supply rail (bar or arrow)
s.gnd(at, kind='earth')             # ground: earth, signal, chassis
s.terminal(at, 'IN')                # terminal / port
s.dot(at)                           # junction dot
```

## Parts and pins

```python
r['1']                 # a Pin: an (x, y) tuple that also knows its part and name
r['2'].offset(20, 0)   # (x + 20, y)
r.pins                 # {'1': Pin, '2': Pin}
r.ref, r.sym, r.id, r.props
r.set(value='4k7')     # change settings / properties
r.move(10, 0); r.moveto(200, 100)
r.bbox                 # [x0, y0, x1, y1] including labels
r.field('Power', '0.5 W', show=True); r.fields; r.remove_field('Power')
s.find('R1'), s['R1']  # look up by reference
s.comps('resistor')    # all parts, or all of one symbol
```

## Wires

```python
s.wire(a, b, c, …, style='')              # a polyline through points / pins
s.route(a, b, how='auto')                 # orthogonal: 'hv', 'vh', 'hvh', 'vhv' or 'auto'
s.connect(p1, p2, p3, how='auto')         # chain routes through several points
w = s.wire(r['2'], (220, 100)); w[-1]     # a Wire is the list of its points
s.wire(reg['Q'], (300, 40), style='bus')  # a bus
```

## Annotation

```python
s.text(x, y, 'Gain stage', cls='lbl', anchor='start')   # text classes: see Styles and themes
s.note(x, y, 'f_{c} = 1 kHz'); s.heading(x, y, 'Front end')
s.rect(x, y, w, h, cls='grp', label='Input', rx=4)      # grp, box, accbox, frame
s.group([r1, c1, u1], label='Filter', pad=12)           # shading behind parts
s.arrow((x1, y1), (x2, y2), style='acc')
s.raw('<circle cx="0" cy="0" r="3"/>', x=100, y=100)    # verbatim SVG
```

## Output

```python
s.save('fig.json'); Schematic.load('fig.json')           # or schematrix.load(path)
s.to_svg(embed_fonts=False); s.save_svg('fig.svg')
s.export('fig.png', scale=3, background=False, ids=None, margin=None, fonts=True)
s.save_png('fig.png', scale=2); s.save_pdf('fig.pdf')
s.to_tikz(standalone=False)
s._repr_svg_()                                           # Jupyter shows a Schematic inline
```

## Netlists and simulation

```python
s.netlist()                      # {'nets': {...}, 'pins': {...}, 'warnings': [...]}
s.spice()                        # SPICE text
s.directive('.tran 1u 1m', '.meas tran vmax MAX v(OUT)')
s.export_netlist('kicad'); s.save_netlist('fig.net')
Schematic.from_netlist('board.net')        # a path or the text
```

See [Netlists](Netlists.md) and [Simulation](Simulation.md).

## In the editor

- Every `Schematic` a script creates opens as a tab; to open only some, call `s.show()` on them.
- `print()` output and tracebacks appear under the script.
- Scripts run in a separate process with a time limit (30 s by default) and, on Linux, memory / CPU limits.
- Old figure scripts based on the `S` class are recognised and imported ([Legacy figure scripts](Legacy-Figure-Scripts.md)).
- [Custom symbols](Custom-Symbols.md) of the workspace are available by name.

## Recipes

A loop:

```python
lad = Schematic('Ladder')
prev = lad.terminal((60, 40), 'I+')['p']
for k, r in enumerate(['10 m\\ohm', '90 m\\ohm', '900 m\\ohm'], 1):
    rk = lad.resistor(anchor='1', at=prev, rot=90, value=r, length=80)
    prev = rk['2']
    lad.flag(lad.wire(prev, prev.offset(60, 0))[-1], f'T{k}', side='right')
```

All figures of a report from one script:

```python
from schematrix import Schematic

def front_end():
    s = Schematic('front-end', theme='formal'); ...; return s
def adc():
    s = Schematic('adc', theme='formal'); ...; return s

for f in (front_end, adc):
    s = f()
    s.export(f'figures/{s.title}.tikz'); s.export(f'figures/{s.title}.pdf')
```
