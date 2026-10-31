# Styles and themes

## Drawing styles (themes)

A document's **theme** sets colours, fonts, line weights and fills for everything on the sheet and in every export.
Pick it in the document inspector (*Theme*, with nothing selected), or in Python with `Schematic(theme='formal')` or
`s.page(theme='formal')`.

| Theme | Look | Good for |
|---|---|---|
| `instrix` (default) | Instrix brand: JetBrains Mono, soft blue-grey fills, blue accent | reports in the house style |
| `instrix-dark` | the same on a dark background | slides, screens |
| `blueprint` | white on blue | presentations |
| `print-mono` | black on white, grey fills | monochrome printing |
| `formal` | Times / LaTeX serif, black, thin even lines, italic references | papers and theses (pairs with [TikZ export](LaTeX.md)) |
| `technical` | Helvetica, black, medium lines | datasheet / IEEE-style figures |
| `kicad` | KiCad's classic colours: dark-red symbols, pale-yellow bodies, green wires | readers used to KiCad |

| | |
|---|---|
| ![instrix](img/themes/instrix.png) | ![formal](img/themes/formal.png) |
| ![technical](img/themes/technical.png) | ![kicad](img/themes/kicad.png) |
| ![instrix-dark](img/themes/instrix-dark.png) | ![blueprint](img/themes/blueprint.png) |
| ![print-mono](img/themes/print-mono.png) | |

The editor shows the sheet in its theme. Palette thumbnails always use the default look.

## Line styles

Each part, wire and arrow can carry a **style** on top of the theme (inspector *Style*, the line-style buttons at the
top right for new items, `E` to toggle accent, or `style=` in Python):

| Style | | Python |
|---|---|---|
| Ink | the theme's normal lines | `style=''` |
| Accent | heavier, in the accent colour; to highlight a signal path | `style='acc'` |
| Dash | dashed; parasitics, optional parts, mechanical links | `style='para'` |
| Accent dash | both | `style='acc para'` |
| Bus | thick; a bus wire (wires only), see [buses](Wires-and-Connections.md#buses) | `style='bus'` |

## Text classes

Free texts (`T` tool, `s.text()`) pick a class in the inspector: Label `lbl`, Reference `ref`, Value `val`, Small value
`valsm`, Node name `node` (italic), Net `net`, Pin sign `pin`, Terminal `termlbl`, Accent label `accl`, Group label
`grplbl`, Note `note` (sans), Title `title`. `s.note()` and `s.heading()` are shortcuts for `note` and `title`.

## Group boxes and frames

The Box tool (`B`, or `s.rect(...)`) draws: **Group shading** (`grp`, a soft background behind related parts),
**Box** (`box`, a filled outline), **Accent box** (`accbox`), **Frame** (`frame`, a thin outline). Boxes have an optional
label in the top-left corner. `s.group([parts], label='Input stage')` sizes a shading box around parts.

## Custom themes

A theme can also be a dictionary that overrides tokens of a base theme; store it in the document (`"theme": {...}`)
or pass it from Python:

```python
s = Schematic('custom', theme={'base': 'formal', 'accent': '#b00020', 'lw': '1.2'})
```

| Token | Meaning | Token | Meaning |
|---|---|---|---|
| `ink` | lines and text | `lw` | normal line width |
| `wire` | wire colour (defaults to ink) | `lw_plate` | heavy lines (plates, accent) |
| `text` | text colour (defaults to ink) | `lw_thin` | thin lines |
| `muted` | values, notes | `lw_body` | body outlines |
| `accent` | accent colour | `lw_bus` | bus wires |
| `accent_fill` | accent box fill | `weight` / `strong` | normal / bold font weights |
| `surface` | group shading, net labels | `ref_style` | `normal` or `italic` references |
| `box` | block fill | `join` | `round` or `miter` line joins |
| `body` | op-amp / source / gate body fill | `mono` | main font stack (CSS) |
| `paper` | background | `sans` | notes and titles font stack |
| `rule` | frames | | |

The editor recolours custom colour tokens live; other tokens apply in exports.
