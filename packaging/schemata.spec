# PyInstaller spec: one-folder native build for Windows and Linux.
#   pip install ".[desktop]" pyinstaller && pyinstaller packaging/schematrix.spec
# Output: dist/Schematrix/Schematrix(.exe). The app opens a native window (pywebview: WebView2 on Windows,
# GTK/Qt WebKit on Linux) and falls back to the default browser.
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

root = os.path.abspath(os.path.join(SPECPATH, '..'))
datas = collect_data_files('schematrix', includes=['web/**/*', 'examples/**/*'])
hidden = collect_submodules('uvicorn') + collect_submodules('schematrix') + ['webview']

a = Analysis([os.path.join(root, 'packaging', 'launcher.py')], pathex=[root], datas=datas, hiddenimports=hidden,
             excludes=['tkinter', 'matplotlib', 'numpy', 'PIL'])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Schematrix', console=False,
          icon=os.path.join(root, 'packaging', 'schematrix.ico') if os.path.exists(os.path.join(root, 'packaging', 'schematrix.ico')) else None)
coll = COLLECT(exe, a.binaries, a.datas, name='Schematrix')
