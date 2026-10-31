# Netlists

A netlist lists the parts and which pins share each net. Schematrix writes and reads three formats:

| Format | Extension | Write | Read |
|---|---|---|---|
| **SPICE** | `.cir` (also `.sp`, `.spi`, `.spice`, `.ckt`) | one line per part from its template, then models and analyses | elements by letter, `.model` types, analyses kept |
| **KiCad** | `.net` (version E, KiCad 6–9) | KiCad library names and pin numbers | by library part, then reference prefix |
| **JSON** | `.netlist.json` | everything, lossless | the same |

Netlists written by Schematrix carry the symbol, settings and [fields](Fields-and-Properties.md) of every part (as
`*@` comments in SPICE, component properties in KiCad), so writing one and reading it back gives the same parts.

## Writing

- Editor: *Export > Netlist: SPICE / KiCad / JSON*, or the Netlist pane's **Download** (pick the format first).
- CLI: `schematrix netlist fig.json -f kicad -o fig.net` (`-f spice|kicad|json`; without `-o` it prints).
- Python: `s.export_netlist('kicad')` (text), `s.save_netlist('fig.net')` (format from the extension), `s.spice()`.
- HTTP: `POST /api/netlist/export?format=kicad` with `{"doc": …}`.

## Reading: a netlist becomes a sheet

- Editor: *File > Import netlist…*, drag a netlist file onto the window, or open one from the workspace.
- CLI: `schematrix import-netlist board.net -f json,svg` (format detected; `--netformat` to force it).
- Python: `Schematic.from_netlist('board.net')` (a path or the text itself).
- HTTP: `POST /api/netlist/import` with `{"text": …, "filename": "board.net"}`.

A netlist has no positions, so the importer **lays the parts out in rows** and gives every connected pin a short wire
with a **net label** (or a ground symbol for `0`, `GND`, `AGND`, …). The drawing therefore has exactly the netlist's
connections; tidy it by hand from there. Single-pin nets with automatic names are left unconnected. Warnings (unknown
parts, pins that don't match) are shown after the import.

### How parts are recognised

| Source | Rule |
|---|---|
| Schematrix-written files | the stored symbol and settings |
| **KiCad** | the library part name: `Device:R`, `Device:C_Polarized`, `Device:D_Zener`, `Device:Q_NPN_BCE`, `74xx:74HC00` (a NAND gate), `74xx:74HC595` (a shift register), `Connector:Conn_01x04_Pin`, … — every symbol and [variant](Symbol-Library.md) knows its KiCad aliases; then the reference prefix (`R`, `C`, `L`, `D`, `Q`, `U`, `J`, `SW`, `K`, `T`, `F`, `Y`, `BT`, `TP`, `LED`, …) |
| **KiCad pins** | the pin function (`B`, `C`, `E`, `G`, `D`, `S`, …), else the pin number via the symbol's KiCad numbering; a part name's suffix such as `_CBE` or `_GDS` gives the pin order |
| **SPICE** | the element letter: `R C L D Q M J V I E G H F` (`X` subcircuits named like an op-amp become op-amps, others blocks); `.model` lines decide NPN / PNP, N / P-channel and diode kinds |
| anything else | a generic **block** with the part's pins |

Parts with bus pins (registers, counters, …) whose netlist lists bits (`D0` … `D7`) are imported with one pin per bit.

## Net names

- Named nets keep their names (labels, rails, grounds, terminals); unnamed ones are `N001`, `N002`, … (never clashing
  with a label's name).
- Bus members are named after the bus: `D[7:0]` → `D0` … `D7` (see [buses](Wires-and-Connections.md#buses)).
- SPICE node names drop spaces, parentheses and markup (`+5 V` → `+5_V`, `V_{OUT}` → `VOUT`); a `*@nets` comment
  remembers the original names for re-import.
- Ground nets are `0` unless a ground symbol's *Net* says otherwise.

## SPICE templates

Each symbol carries a SPICE line template; a symbol without one is written as a comment (`* K1: Relay (no SPICE
model)`). Templates use:

| Placeholder | Becomes |
|---|---|
| `{1}`, `{A}`, `{inp}` | the net on that pin |
| `{a\|b}` | pin *a* if the symbol has it, else *b* (`{B\|S}`: a MOSFET's bulk, or its source) |
| `{pin?}` | the net, or nothing if the pin is absent (optional pins) |
| `{*}` | every pin in order (subcircuits) |
| `{value}` | the value in SPICE units (`10 k\ohm` → `10k`, `4.7 µF` → `4.7u`, `2.2 MΩ` → `2.2Meg`) |
| `{model}` | the part number, else the symbol's default model (`DMOD`, `NPN`, `NMOS`, `OPAMP`, …) |
| `{src}` | a source spec: a plain number becomes `DC 5` / `AC 1` by the source kind; anything else (`SIN(0 1 1k)`, `PULSE(…)`) is used as written |
| `{ctrl}` | the controlling source of a current-controlled source |

Examples: resistor `R {1} {2} {value}`, diode `D {A} {K} {model}`, MOSFET `M {D} {G} {S} {B|S} {model}`, op-amp
`X {inp} {inm} {vp?} {vn?} {out} {model}`. [Custom symbols](Custom-Symbols.md) can have their own.

## KiCad numbering

KiCad identifies pins by number. Schematrix uses KiCad's conventions where they exist: diode 1 = K, 2 = A;
transistors `Q_NPN_BCE` (1 = B, 2 = C, 3 = E); MOSFETs `Q_NMOS_GDS`; potentiometer 1 / W = 2 / 3; op-amp 1 = out,
2 = −, 3 = +, 4 = V−, 8 = V+; otherwise numeric pin names as they are, or 1, 2, 3 … in pin order.

## The JSON netlist

```json
{"format": "schematrix-netlist", "version": 1, "title": "amp",
 "components": [{"ref": "R1", "symbol": "resistor", "value": "10k", "part": "", "props": {},
                 "fields": {"Tolerance": "1%"}, "pins": {"1": "VIN", "2": "N001"}}],
 "nets": [{"name": "VIN", "nodes": [["R1", "1"]]}],
 "spice": [".tran 1u 1m"]}
```

On reading, a component's `pins` wins; without it, the `nets` list is used.
