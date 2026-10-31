# Custom symbols

When no built-in symbol fits, draw your own in the **symbol editor**. Custom symbols behave like built-in ones: they
sit in the palette (category *Custom*, marked ✎), have pins that connect and appear in netlists, carry a reference
prefix and suggested fields, can have a SPICE line, and are usable from scripts by name.

![Symbol editor](img/symbol-editor.png)

## Opening the editor

- **File > New symbol…** — an empty symbol.
- **Right-click a palette tile** — a built-in symbol: start a custom copy of it; a custom symbol: edit it.
- **Select a part** on the sheet, then *Customise symbol…* in the inspector (built-in: a copy of its current drawing,
  and the part switches to the new symbol when you save) or *Edit symbol…* (custom).
- **Start from…** (top bar) replaces the drawing with a copy of any built-in symbol.

## Drawing

| Tool | Key | |
|---|---|---|
| Select | `V` | click to select; drag to move; drag a round handle to reshape (line corners, rectangle corner, circle radius) |
| Line | `L` | click points; `Enter` or double-click ends; `Backspace` removes the last point |
| Shape | `G` | like Line, but closed and filled |
| Rectangle | `R` | drag |
| Circle | `C` | drag from the centre |
| Text | `T` | click, then type in the side panel (markup works) |
| Pin | `P` | click where a wire should connect; rename in the side panel |

Everything snaps to the grid (5, 2.5 or 1 units; parts are normally laid out on 5). Delete with `Del`, duplicate with
`Ctrl D`, nudge with the arrow keys, undo with `Ctrl Z`, zoom with the wheel, pan with the right button, `F` to fit.

The side panel sets, for the selected item: line **stroke** (normal, heavy, thin, dashed), shape **fill** (none, paper,
surface, ink), rectangle corner radius, text style / anchor / centring, pin name and position, and *To front / To
back / Delete*.

### Conventions that make a symbol behave like the built-ins

- Put **pins at the ends of the leads**, on the 5-unit grid, with the lead drawn as a line from the body to the pin.
- Two-terminal parts lie along +x with pin 1 on the left; keep the origin (the crosshair) near the middle.
- Use the *Normal* stroke for leads and outlines, *Heavy* for plates and bars, *Surface* fill for block bodies.
- Place the label block (**REF / value** marker: drag it, or use *Label block: Above / Below / Left / Right*) where it
  won't hit wires.

## Symbol settings

| Setting | |
|---|---|
| Name (id) | lower-case letters, digits and `_` (e.g. `ldo_3v3`); the Python method name; cannot be a built-in name |
| Title | the palette and inspector name |
| Category | palette category (default *Custom*) |
| Reference prefix | `U`, `R`, `K`, … for automatic references |
| Description | tooltip text |
| Suggested fields | offered as one-click fields in the inspector |
| SPICE line | optional template, e.g. `X {IN} {GND} {OUT} {model}` ([templates](Netlists.md#spice-templates)) |

**Save to library** stores it; **Save as…** stores a copy under a new name; **Delete** removes it from the library
(sheets that use it keep their own copy).

## Where symbols live

- A custom symbol is a JSON file in the workspace's `symbols/` folder (`~/Schematrix/symbols/ldo_3v3.json`). Copy
  these files to share a library; the editor picks up new or changed files when it loads the catalogue.
- **Every sheet that uses a custom symbol stores a copy of it** (`"symbols"` in the document), so the sheet opens and
  renders correctly on a machine that does not have the symbol in its library.
- Scripts run by the editor or the CLI see the workspace's symbols by name: `s.ldo_3v3((100, 50))`.

## The file format

```json
{"name": "ldo_3v3", "title": "3.3 V LDO", "category": "Custom", "prefix": "U",
 "prims": [{"k": "rc", "x": -30, "y": -20, "w": 60, "h": 40, "c": "box", "rx": 2},
           {"k": "pl", "pts": [[-40, 0], [-30, 0]], "c": "w"},
           {"k": "pl", "pts": [[30, 0], [40, 0]], "c": "w"},
           {"k": "pl", "pts": [[0, 20], [0, 30]], "c": "w"},
           {"k": "tx", "x": 0, "y": 0, "s": "LDO", "c": "valsm", "a": "middle", "ctr": true}],
 "pins": {"IN": [-40, 0], "OUT": [40, 0], "GND": [0, 30]},
 "label": {"x": 0, "y": -26, "nx": 0, "ny": -1},
 "spice": "X {IN} {GND} {OUT} {model}", "fields": ["Output voltage"], "help": ""}
```

| Primitive | Keys |
|---|---|
| `pl` polyline | `pts`, `c` (`w`, `w plate`, `w thin`, `w para`, `w bus`) |
| `pg` polygon | `pts`, `c` (`amp` paper, `box` surface, `dot` ink, `w` none) |
| `rc` rectangle | `x`, `y`, `w`, `h`, `rx`, `c` |
| `ci` circle | `x`, `y`, `r`, `c` |
| `tx` text | `x`, `y`, `s`, `c` (`lbl`, `ref`, `val`, `valsm`, `pin`), `a` (`start` / `middle` / `end`), `ctr` (centred vertically) |

`label` is where the reference / value / part block sits and its outward direction (`nx`, `ny`): (0, −1) above,
(0, 1) below, (1, 0) right, (−1, 0) left.

## From Python

```python
from schematrix.symbols import custom
custom.define('ldo_3v3', title='3.3 V LDO', prefix='U',
              prims=[...], pins={'IN': [-40, 0], 'OUT': [40, 0], 'GND': [0, 30]})
s.ldo_3v3((200, 100), value='3.3 V')

custom.load_dir('my-symbols/')            # register a folder of .json definitions
d = custom.from_builtin('npn', {'envelope': True}, 'npn_round')   # a definition copied from a built-in
```

Custom symbols are not available on a [public server](Deployment.md#public-server).
