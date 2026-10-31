# Command line

```
schematrix [app]            open the editor in an app window (the default)
schematrix serve            run the web server
schematrix render           render documents or scripts to files
schematrix netlist          write a netlist
schematrix import-netlist   draw a schematic from a netlist
schematrix import-legacy    convert an old S-class figure script
schematrix symbols          list the symbol library
```

## app

```bash
schematrix                                  # same as: schematrix app
schematrix app --engine chromium            # auto | chromium | webview | browser
schematrix app --workspace ~/projects/afe   # another workspace folder
schematrix app --port 9000
```

Starts a local server and opens a window (see [Installation](Installation.md#opening-the-app)). With no `--port` or
`--workspace` and an instance already running, it opens another window on it.

## serve

```bash
schematrix serve                            # http://127.0.0.1:8000
schematrix serve --host 0.0.0.0 --port 8000 --workspace /srv/schematrix --open
```

Environment variables configure it (`SCHEMATRIX_TOKEN`, `SCHEMATRIX_SCRIPTS`, `SCHEMATRIX_PUBLIC`, …); see
[Deployment](Deployment.md).

## render

```bash
schematrix render INPUT [-o OUTPUT] [-f FORMATS] [--fonts] [--background B] [--scale S] [--margin M]
```

- **INPUT**: a `.json` document, or a `.py` script (every schematic it creates or shows), or an old figure script.
- **-o**: a file (one result; the format comes from its extension) or a folder (default: the current one; files are
  named after the schematics' titles).
- **-f**: comma list of `svg png jpg webp pdf eps tikz tex json cir net` (default `svg`).
- **--fonts**: embed the fonts in SVG files.
- **--background**: `paper` (the theme's, default), `none` / `transparent`, or a colour like `"#ffffff"`.
- **--scale**: bitmap scale, 2 = 192 dpi (default 2).
- **--margin**: crop margin around the drawing.

```bash
schematrix render amp.json -o amp.pdf
schematrix render figures.py -o out/ -f svg,pdf,tikz
schematrix render amp.json -o amp.png --scale 4 --background none
```

## netlist

```bash
schematrix netlist INPUT [-f spice|kicad|json] [-o FILE]
schematrix netlist amp.json                      # SPICE to the terminal
schematrix netlist board.py -f kicad -o board.net
```

## import-netlist

```bash
schematrix import-netlist INPUT [--netformat spice|kicad|json] [-o STEM] [-f json,svg,png,pdf] [--fonts]
schematrix import-netlist board.net              # -> board.json and board.svg
```

## import-legacy

```bash
schematrix import-legacy schematics.py -o figs/ -f json,svg
```

Runs an old figure script built on the hand-rolled `S` class and writes each figure as an editable document (and
any other formats). See [Legacy figure scripts](Legacy-Figure-Scripts.md).

## symbols

```bash
schematrix symbols        # name, title, pins and settings of every symbol
```
