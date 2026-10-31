# PyInstaller spec: one-folder native build for Windows, Linux and macOS.
#   pip install ".[desktop]" pyinstaller && pyinstaller packaging/schematrix.spec
# Output: dist/Schematrix/Schematrix(.exe), and dist/Schematrix.app on macOS. The app opens a native window
# (pywebview: WebView2 on Windows, Cocoa WebKit on macOS, GTK/Qt WebKit on Linux, or a Chromium app window on Linux
# when one is installed) and falls back to the default browser. packaging/package.py turns the output into
# installers (AppImage, .deb, setup .exe, .zip, .dmg).
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

root = os.path.abspath(os.path.join(SPECPATH, '..'))
sys.path.insert(0, root)
from schematrix import __version__      # noqa: E402

datas = collect_data_files('schematrix', includes=['web/**/*', 'examples/**/*']) + [(os.path.join(root, 'LICENSE'), '.')]
hidden = (collect_submodules('uvicorn') + collect_submodules('schematrix') + ['webview', 'brotli']
          + collect_submodules('fontTools.ttLib') + collect_submodules('fontTools.pens'))   # text outlines; tables load lazily
icon = os.path.join(root, 'packaging', 'schematrix.icns' if sys.platform == 'darwin' else 'schematrix.ico')


def cairo():
    """Windows / macOS: ship Cairo (PDF / PNG export) so users install nothing. cairosvg loads it at run time, which
    PyInstaller cannot see, so it is added by hand; PyInstaller then collects the libraries it links to.
    Linux uses the system's libcairo2 (every desktop has it; the .deb depends on it)."""
    if sys.platform == 'win32':
        name, dirs = 'libcairo-2.dll', os.environ.get('PATH', '').split(os.pathsep)
    elif sys.platform == 'darwin':
        name, dirs = 'libcairo.2.dylib', ['/opt/homebrew/lib', '/usr/local/lib']
    else:
        return []
    for d in dirs:
        if d and os.path.isfile(os.path.join(d, name)):
            return [(os.path.join(d, name), '.')]
    if os.environ.get('SCHEMATRIX_REQUIRE_CAIRO'):
        raise SystemExit(f'{name} not found: install Cairo (MSYS2 on Windows, Homebrew on macOS) before building')
    print(f'WARNING: {name} not found; this build will not export PDF / PNG without a system Cairo')
    return []


a = Analysis([os.path.join(root, 'packaging', 'launcher.py')], pathex=[root], binaries=cairo(), datas=datas,
             hiddenimports=hidden,
             excludes=['tkinter', 'matplotlib', 'numpy'])      # PIL stays: cairosvg (PNG/PDF) imports it
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Schematrix', console=False, icon=icon)
coll = COLLECT(exe, a.binaries, a.datas, name='Schematrix')
if sys.platform == 'darwin':
    app = BUNDLE(coll, name='Schematrix.app', icon=icon, bundle_identifier='io.github.instrix.schematrix',
                 info_plist={'CFBundleShortVersionString': __version__, 'CFBundleVersion': __version__,
                             'NSHighResolutionCapable': True})
