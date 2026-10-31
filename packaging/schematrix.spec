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

datas = collect_data_files('schematrix', includes=['web/**/*', 'examples/**/*'])
hidden = collect_submodules('uvicorn') + collect_submodules('schematrix') + ['webview']
icon = os.path.join(root, 'packaging', 'schematrix.icns' if sys.platform == 'darwin' else 'schematrix.ico')

a = Analysis([os.path.join(root, 'packaging', 'launcher.py')], pathex=[root], datas=datas, hiddenimports=hidden,
             excludes=['tkinter', 'matplotlib', 'numpy'])      # PIL stays: cairosvg (PNG/PDF) imports it
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Schematrix', console=False, icon=icon)
coll = COLLECT(exe, a.binaries, a.datas, name='Schematrix')
if sys.platform == 'darwin':
    app = BUNDLE(coll, name='Schematrix.app', icon=icon, bundle_identifier='io.github.instrix.schematrix',
                 info_plist={'CFBundleShortVersionString': __version__, 'CFBundleVersion': __version__,
                             'NSHighResolutionCapable': True})
