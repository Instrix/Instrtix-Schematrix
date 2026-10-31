# Schematrix wiki

Schematrix is an electrical schematic editor in the Instrix house style, with a Python scripting library behind it.
The same core draws, netlists and serves the editor, so a schematic drawn by hand and one built by a script are the
same kind of document. Drawings export to SVG, PNG, JPEG, WebP, PDF, EPS and TikZ, and netlists to SPICE, KiCad and
JSON.

Schematrix is free and open source under the GNU GPL v3 or later, and free forever: no payments, no subscriptions,
no locked features.

![The editor](img/editor.png)

## Start here

| | |
|---|---|
| [Installation](Installation.md) | pipx, a virtual environment, from a clone, Docker, native builds |
| [Getting started](Getting-Started.md) | your first schematic in ten minutes |
| [The editor](Editor.md) | every panel, tool and menu |
| [Keyboard and mouse](Keyboard-and-Mouse.md) | all shortcuts on one page |

## Drawing

| | |
|---|---|
| [Wires and connections](Wires-and-Connections.md) | wires, junctions, hops, net labels, rails, grounds, buses |
| [Symbol library](Symbol-Library.md) | every built-in symbol with its pins, settings and variants (generated) |
| [Fields and properties](Fields-and-Properties.md) | references, values, part numbers, your own fields |
| [Text markup](Text-Markup.md) | overbars, subscripts, Ω, µ, Greek letters in any text |
| [Styles and themes](Styles-and-Themes.md) | the seven drawing styles, accent / dashed / bus line styles, custom themes |
| [Page frames](Page-Frames.md) | paper sizes, borders and title blocks |
| [Custom symbols](Custom-Symbols.md) | the symbol editor and the symbol file format |

## Output

| | |
|---|---|
| [Exporting](Exporting.md) | every format, selection-only export, backgrounds, resolution |
| [Using Schematrix in LaTeX](LaTeX.md) | TikZ and PDF figures in papers and theses, step by step |
| [Netlists](Netlists.md) | SPICE, KiCad and JSON netlists, both ways |
| [Simulation](Simulation.md) | SPICE analyses, default models, running ngspice |

## Automation and reference

| | |
|---|---|
| [Python scripting](Python-Scripting.md) | the `Schematic` API, with examples |
| [Command line](Command-Line.md) | `schematrix render`, `netlist`, `import-netlist`, … |
| [HTTP API](HTTP-API.md) | every server endpoint |
| [Document format](Document-Format.md) | the `.json` file, element by element |
| [Examples](Examples.md) | the bundled example sheets |
| [Legacy figure scripts](Legacy-Figure-Scripts.md) | importing the old TR-0002 `S`-class scripts |

## Running it for others

| | |
|---|---|
| [Deployment](Deployment.md) | Docker, private (token) and public (anonymous) servers, HTTPS, backups |
| [Troubleshooting](Troubleshooting.md) | common problems and their fixes |
| [Development](Development.md) | code layout, tests, adding symbols, releases |
