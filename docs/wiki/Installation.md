# Installation

Schematrix needs **Python 3.10 or newer**. It is not on PyPI; it installs straight from the (private) GitHub
repository, so pip needs your GitHub access: an SSH key (`git+ssh://`, used below) or HTTPS with a personal access
token (`git+https://<token>@github.com/...`).

## Which way?

| You want to… | Use |
|---|---|
| use the editor as an app | [pipx](#pipx-recommended-for-the-app) |
| write Python scripts / notebooks that `import schematrix` | [a virtual environment](#pip-in-a-virtual-environment) |
| change Schematrix itself | [a clone](#from-a-clone-development) |
| run it on a server for a team or the public | [Docker](Deployment.md) |
| a double-click app without Python | a [native build](#native-builds) |

## Extras

| Extra | Adds | Needed for |
|---|---|---|
| *(none)* | editor, server, scripting, SVG / SPICE / TikZ export | always enough to work |
| `export` | `cairosvg`, `pillow` | PDF, EPS and server-side PNG / JPEG / WebP (the editor can make bitmaps in the browser without it) |
| `desktop` | `pywebview`, `cairosvg` | the app window when no Chromium-family browser is installed |
| `dev` | `pytest`, `httpx`, `pillow`, `numpy` | running the tests |

## pipx (recommended for the app)

[pipx](https://pipx.pypa.io) installs the `schematrix` command in its own environment and puts it on your PATH.

```bash
pipx install "schematrix[desktop] @ git+ssh://git@github.com/Instrix/instrtix-schematrix.git"
schematrix                      # opens the editor
pipx upgrade schematrix         # update to the latest main (use pipx install --force if it says "up to date")
```

Pin a release with `...instrtix-schematrix.git@v0.2.0`.

## pip in a virtual environment

```bash
python3 -m venv .venv && source .venv/bin/activate          # Windows: py -m venv .venv; .venv\Scripts\Activate.ps1
pip install "schematrix[export] @ git+ssh://git@github.com/Instrix/instrtix-schematrix.git"
python -c "import schematrix; print(schematrix.__version__)"
```

In a `requirements.txt`:

```
schematrix[export] @ git+ssh://git@github.com/Instrix/instrtix-schematrix.git@v0.2.0
```

## From a clone (development)

```bash
git clone git@github.com:Instrix/instrtix-schematrix.git && cd instrtix-schematrix
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,desktop]"         # editable: code changes apply without reinstalling
pytest -q
```

## Opening the app

`schematrix` (or `schematrix app`) starts a local server and opens a window:

| Platform | Window |
|---|---|
| Linux | a Chromium / Chrome / Brave / Edge app window if one is installed (fastest), else the GTK WebKit window, else your browser |
| Windows | Edge WebView2 (preinstalled on Windows 10 / 11) |
| macOS | the system WebKit |

Choose explicitly with `schematrix app --engine chromium|webview|browser` (or `SCHEMATRIX_ENGINE`). The app uses port
47815 so the editor's browser storage (autosave, settings) survives restarts; starting it a second time opens another
window on the running instance. `schematrix serve --open` runs only the web server and opens your browser.

## Platform notes

- **Linux, GTK window**: install the WebKitGTK bindings: Debian / Ubuntu `sudo apt install python3-gi gir1.2-webkit2-4.1`,
  Fedora `python3-gobject webkit2gtk4.1`, Arch `python-gobject webkit2gtk-4.1`. Schematrix finds them even from a
  pipx or venv install, as long as that uses the system Python. Or use Qt:
  `pipx inject schematrix qtpy pyqt6 pyqt6-webengine`.
- **PNG / PDF that match the editor**: server-side exports use system fonts. Install the editor's fonts for an exact
  match: `sudo apt install fonts-jetbrains-mono fonts-inter` (the Docker image has them).
- **Windows, PDF export**: `cairosvg` needs the Cairo DLL. If PDF export reports a missing `libcairo-2.dll`, install
  GTK3 for Windows (or MSYS2's `mingw-w64-x86_64-cairo`) and put its `bin` folder on PATH. PNG still works from the
  editor without it.
- **macOS**: `brew install cairo` for PDF export.
- **Simulation**: install [ngspice](https://ngspice.sourceforge.io/) to run the SPICE netlists (`sudo apt install ngspice`).
- **LaTeX**: any TeX distribution with TikZ (TeX Live, MiKTeX, Overleaf) compiles the TikZ exports.

## Native builds

```bash
pip install ".[desktop]" pyinstaller
pyinstaller packaging/schematrix.spec       # -> dist/Schematrix/Schematrix(.exe)
```

The release workflow builds the Windows, Linux and macOS bundles and the Docker image on every `v*` tag (or on demand
from GitHub's Actions tab). See [Development](Development.md#releases).
