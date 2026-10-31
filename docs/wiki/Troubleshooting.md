# Troubleshooting

### `schematrix` opens my browser instead of a window

It prints why. On Linux, install Chrome / Chromium (the fastest window) or the GTK WebKit bindings
(`sudo apt install python3-gi gir1.2-webkit2-4.1`), or add Qt (`pipx inject schematrix qtpy pyqt6 pyqt6-webengine`).
See [Installation](Installation.md#platform-notes).

### The desktop app feels slower than the browser

On Linux the GTK WebKit window is slower than Chromium. Install Chrome / Chromium and the app uses it automatically
(`--engine chromium` to force it).

### My autosaved work is gone after restarting the app

Autosave lives in the window's browser storage, tied to the server's address. The app uses a fixed port (47815) so
it survives restarts; if something else occupies that port the app picks another one and the old autosave is not
visible. Save to the workspace (`Ctrl S`) for anything you want to keep.

### PDF / EPS export says it needs cairosvg

Only pip installs can hit this; the downloads include it. Install the `export` extra:
`pipx inject schematrix cairosvg pillow` (pipx) or `pip install cairosvg pillow`. On Windows and macOS, if it then
reports a missing Cairo library, install the Schematrix app as well: a pip install uses the app's Cairo. PNG, JPEG and
WebP from the editor work without any of it.

### Exported PNG / PDF text looks different from the editor, or shows boxes

Server-side exports use the server's fonts. Install the theme's fonts (`fonts-jetbrains-mono fonts-inter` for the
default theme; Times New Roman or Liberation Serif for `formal`), or export the PNG from the editor (drawn by the
browser), or use SVG with embedded fonts.

### A wire looks connected but the netlist says the pin is unconnected

Wires connect at ends, corners and pins, not where they merely cross. Zoom in: the end should sit exactly on the pin
(the wire tool shows a ring when it snaps). A dot marks real three-way connections. Plain wires never connect to a
**bus** except through names ([buses](Wires-and-Connections.md#buses)).

### Two nets merged unexpectedly

Two labels with the same text are the same net, anywhere on the sheet. Ground symbols are all net `0` unless their
*Net* setting differs.

### "net named both … and …"

One net carries two different labels; rename one, or check for an accidental connection.

### A part I placed has the wrong pins after changing a setting

Settings marked *shape* (e.g. *inputs*, *bits*, *Bus pins*) change the drawing and its pins; wires on pins that moved or
disappeared are no longer connected. Re-route them.

### Script errors

The traceback appears under the script. Common: forgetting to double a backslash in markup (`'10 k\\ohm'`), unknown
settings (the error lists the valid ones), or the 30-second time limit (`SCHEMATRIX_SCRIPT_TIMEOUT`).

### "this server has no token, so it only answers to localhost"

A server with neither a token nor public mode runs scripts for whoever reaches it, so it refuses requests addressed to
any name but `localhost` / `127.0.0.1` (this keeps web sites from reaching the desktop app through DNS rebinding).
To use it from other computers, set `SCHEMATRIX_TOKEN` (recommended), or list the names it is reached by in
`SCHEMATRIX_ALLOWED_HOSTS` (e.g. `schematrix.lan,192.168.1.20`) if everyone on that network is trusted.

### "custom symbols are not available on this public server"

The sheet uses [custom symbols](Custom-Symbols.md); public servers don't accept them. Use a private server or the
desktop app.

### ngspice: "no such vector" / no AC results

Name the nets you measure with labels (`OUT`, then `v(OUT)`); SPICE node names drop spaces and markup (`V_{OUT}` →
`VOUT`). For `.ac` runs, Schematrix adds `.save all`; if you added your own `.save`, include the vectors you measure.

### LaTeX: `Undefined control sequence` in a TikZ figure

Add `\usepackage{tikz}`; for `\resizebox` also `\usepackage{graphicx}`. See [LaTeX](LaTeX.md).

### pipx upgrade says it is already up to date

Installs from git are pinned to the commit; reinstall:
`pipx install --force "schematrix[desktop] @ git+https://github.com/Instrix/Instrtix-Schematrix.git"`.
