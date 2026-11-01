# Installation

## Download the app

| System | Download | |
|---|---|---|
| Windows 10 / 11 | [Schematrix-Setup.exe](https://github.com/Instrix/Instrtix-Schematrix/releases/latest/download/Schematrix-Setup.exe) | installer; or the portable [.zip](https://github.com/Instrix/Instrtix-Schematrix/releases/latest/download/Schematrix-windows.zip) |
| Linux (any, x86-64) | [Schematrix-x86_64.AppImage](https://github.com/Instrix/Instrtix-Schematrix/releases/latest/download/Schematrix-x86_64.AppImage) | `chmod +x` and run |
| Debian / Ubuntu | [schematrix_amd64.deb](https://github.com/Instrix/Instrtix-Schematrix/releases/latest/download/schematrix_amd64.deb) | `sudo apt install ./schematrix_amd64.deb` |
| macOS (Apple silicon) | [Schematrix-macos.dmg](https://github.com/Instrix/Instrtix-Schematrix/releases/latest/download/Schematrix-macos.dmg) | drag to Applications; unsigned: first open with right-click > Open |

Each includes its own Python, the editor, the `schematrix` command line and PDF / PNG export. Older versions and
checksums: [Releases](https://github.com/Instrix/Instrtix-Schematrix/releases).

## With Python

Schematrix needs **Python 3.10 or newer**. pip installs it straight from the GitHub repository (below), or from the
wheel attached to each release. It is not on PyPI yet.

## Which way?

| You want to… | Use |
|---|---|
| use the editor as an app | [pipx](#pipx-recommended-for-the-app) |
| write Python scripts / notebooks that `import schematrix` | [a virtual environment](#pip-in-a-virtual-environment) |
| change Schematrix itself | [a clone](#from-a-clone-development) |
| run it on a server for a team or the public | [Docker](Deployment.md) |
| a double-click app without Python | a [download](#download-the-app) |

## Extras

| Extra | Adds | Needed for |
|---|---|---|
| *(none)* | editor, server, scripting, SVG / SPICE / TikZ export | always enough to work |
| `export` | `cairosvg`, `pillow`, `fonttools`, `brotli` | PDF, EPS and server-side PNG / JPEG / WebP (the editor can make bitmaps in the browser without it) |
| `desktop` | `pywebview`, `cairosvg`, `fonttools`, `brotli` | the app window when no Chromium-family browser is installed |
| `dev` | `pytest`, `httpx`, `pillow`, `numpy` | running the tests |

## pipx (recommended for the app)

[pipx](https://pipx.pypa.io) installs the `schematrix` command in its own environment and puts it on your PATH.

```bash
pipx install "schematrix[desktop] @ git+https://github.com/Instrix/Instrtix-Schematrix.git"
schematrix                      # opens the editor
pipx upgrade schematrix         # update (pipx install --force if it says "up to date")
```

Pin a release by adding its tag: `"schematrix[desktop] @ git+https://github.com/Instrix/Instrtix-Schematrix.git@v0.2.6"`.

## pip in a virtual environment

```bash
python3 -m venv .venv && source .venv/bin/activate          # Windows: py -m venv .venv; .venv\Scripts\Activate.ps1
pip install "schematrix[export] @ git+https://github.com/Instrix/Instrtix-Schematrix.git"
python -c "import schematrix; print(schematrix.__version__)"
```

In a `requirements.txt`:

```
schematrix[export] @ git+https://github.com/Instrix/Instrtix-Schematrix.git@v0.2.6
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
- **Fonts**: nothing to install. PDF / PNG exports draw their text from the fonts bundled with Schematrix.
- **Windows**: the download needs nothing else. It carries Cairo (PDF / PNG export), and the window uses WebView2,
  which is part of Windows 10 and 11; the installer adds it on the rare machine without it. A pip-installed
  Schematrix borrows the installed app's Cairo, so for PDF / PNG from Python install the app too.
- **macOS**: the download needs nothing else (it carries Cairo; the window is the system WebKit). With pip, PDF / PNG
  export uses the installed app's Cairo, or Homebrew's (`brew install cairo`).
- **Linux downloads** use the system's Cairo (`libcairo2`), which every desktop has; the .deb installs it if missing.
- **Simulation**: install [ngspice](https://ngspice.sourceforge.io/) to run the SPICE netlists (`sudo apt install ngspice`).
- **LaTeX**: any TeX distribution with TikZ (TeX Live, MiKTeX, Overleaf) compiles the TikZ exports.

## Native builds

The downloads are built by CI; to build one yourself on the target system:

```bash
pip install ".[desktop]" pyinstaller
pyinstaller packaging/schematrix.spec       # -> dist/Schematrix/Schematrix(.exe), dist/Schematrix.app on macOS
python packaging/package.py                 # -> dist/release/: AppImage + .deb, setup .exe + .zip, or .dmg
```

`package.py` needs `dpkg-deb` on Linux (appimagetool is downloaded), Inno Setup on Windows. See
[Development](Development.md#releases).
