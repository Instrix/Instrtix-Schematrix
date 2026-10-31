# Document format

A schematic is one JSON file. It is plain text, so it diffs well in version control; the editor, the scripting API and
the server all read and write the same structure.

```json
{
 "version": 1,
 "meta": {"title": "RC low-pass", "description": ""},
 "page": {"width": null, "height": null, "auto": true, "margin": 20, "grid": 5,
          "junctions": true, "hops": false, "x": 0, "y": 0},
 "theme": "instrix",
 "spice": [".ac dec 20 10 1Meg"],
 "symbols": {},
 "elements": [
  {"id": "e1", "type": "comp", "sym": "resistor", "x": 100, "y": 100, "rot": 0, "mirror": false,
   "props": {"ref": "R1", "value": "1 k\\ohm"}, "style": "",
   "fields": [{"name": "Tolerance", "value": "1%", "show": true}]},
  {"id": "e2", "type": "wire", "points": [[130, 100], [200, 100]], "style": ""},
  {"id": "e3", "type": "text", "x": 60, "y": 230, "text": "note", "cls": "note", "anchor": "start"}
 ]
}
```

## Top level

| Key | |
|---|---|
| `version` | format version (1) |
| `meta` | `title`, `description` |
| `page` | `auto` (size to the drawing + `margin`) or fixed `x`, `y`, `width`, `height`; `grid`; `junctions` (dots on); `hops` (wire hops on); `frame` (`{size, orientation, fields}` when a [page frame](Page-Frames.md) is set) |
| `theme` | a theme name, or a dict of token overrides with an optional `base` ([Styles and themes](Styles-and-Themes.md)) |
| `spice` | lines appended to SPICE netlists ([Simulation](Simulation.md)) |
| `symbols` | definitions of the [custom symbols](Custom-Symbols.md) the sheet uses (written on save) |
| `elements` | the drawing, in drawing order (later = on top) |

## Elements

Every element has a unique `id` and a `type`.

### `comp` — a part or net symbol

| Key | |
|---|---|
| `sym` | symbol name ([Symbol library](Symbol-Library.md)) |
| `x`, `y`, `rot`, `mirror` | placement: rotation clockwise 0 / 90 / 180 / 270; mirror flips left-right first |
| `props` | `ref`, `value`, `part` and the symbol's settings (only those that differ from the defaults) |
| `fields` | `[{"name", "value", "show"}]` user fields |
| `style` | `""`, `"acc"`, `"para"`, `"acc para"` |
| `label_offset` | `[dx, dy]` the label block was dragged by |
| `hide_labels` | `true` hides reference / value / part |

### `wire` and `arrow`

`points` (`[[x, y], …]`, at least two) and `style` (`""`, `"acc"`, `"para"`, `"bus"` for wires). Arrows end in an
arrowhead.

### `text`

`x`, `y` (baseline), `text` (newlines allowed, [markup](Text-Markup.md)), `cls` (text class), `anchor` (`start`,
`middle`, `end`).

### `rect`

`x`, `y`, `w`, `h`, `cls` (`grp` shading, `box`, `accbox`, `frame`), `label`, `rx` (corner radius).

### `raw`

`svg` (verbatim markup, kept from legacy figures), `x`, `y` offset, optional `bbox`.

### Frame and lock flags

Elements generated for a page frame carry `"frame": true` and `"locked": true` (and texts of the title block
`"field": "title"` etc.). Locked elements cannot be selected in the editor.

## Notes

- Unknown keys are kept, so newer files open in older versions without losing data.
- Coordinates are drawing units (96 per inch); numbers may be fractional.
- The editor also accepts the JSON netlist format (`"format": "schematrix-netlist"`) and imports it as a new sheet.
