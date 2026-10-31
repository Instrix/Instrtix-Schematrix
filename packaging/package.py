"""Turn the PyInstaller output into the files people download.

    pyinstaller packaging/schematrix.spec --noconfirm
    python packaging/package.py            # packages for the running OS into dist/release/

Linux: Schematrix-x86_64.AppImage and schematrix_amd64.deb (needs dpkg-deb; appimagetool is downloaded if missing).
Windows: Schematrix-Setup.exe (needs Inno Setup's ISCC) and Schematrix-windows.zip.
macOS: Schematrix-macos.dmg (hdiutil).
The names carry no version so that .../releases/latest/download/<name> always points at the newest release.
"""
import os
import platform
import shutil
import stat
import subprocess
import sys
import urllib.request
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PKG = os.path.join(ROOT, 'packaging')
DIST = os.path.join(ROOT, 'dist')
OUT = os.path.join(DIST, 'release')
BUNDLE = os.path.join(DIST, 'Schematrix')
sys.path.insert(0, ROOT)
from schematrix import __version__ as VERSION      # noqa: E402

DESKTOP = """[Desktop Entry]
Type=Application
Name=Schematrix
GenericName=Schematic editor
Comment=Electrical schematic editor and Python scripting library
Exec={exec} %F
Icon=schematrix
Terminal=false
Categories=Development;Electronics;Engineering;
Keywords=schematic;circuit;electronics;spice;netlist;tikz;
StartupWMClass=Schematrix
"""
APPIMAGETOOL = 'https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage'


def run(*cmd, **kw):
    print('+', ' '.join(cmd), flush=True)
    subprocess.run(cmd, check=True, **kw)


def write(path, text, mode=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='\n') as f:
        f.write(text)
    if mode:
        os.chmod(path, mode)


def fresh(path):
    shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path)
    return path


# ---------------------------------------------------------------- Linux
def appimage():
    app = fresh(os.path.join(DIST, 'AppDir'))
    shutil.copytree(BUNDLE, os.path.join(app, 'usr', 'lib', 'schematrix'))
    write(os.path.join(app, 'AppRun'), '#!/bin/sh\nexec "$APPDIR/usr/lib/schematrix/Schematrix" "$@"\n', 0o755)
    write(os.path.join(app, 'schematrix.desktop'), DESKTOP.format(exec='Schematrix'))
    shutil.copy(os.path.join(PKG, 'schematrix.png'), os.path.join(app, 'schematrix.png'))
    shutil.copy(os.path.join(PKG, 'schematrix.png'), os.path.join(app, '.DirIcon'))
    tool = shutil.which('appimagetool')
    if not tool:
        tool = os.path.join(DIST, 'appimagetool')
        if not os.path.exists(tool):
            urllib.request.urlretrieve(APPIMAGETOOL, tool)
        os.chmod(tool, os.stat(tool).st_mode | stat.S_IEXEC)
    # extract-and-run: works where FUSE is missing (CI runners, containers)
    run(tool, '--no-appstream', app, os.path.join(OUT, 'Schematrix-x86_64.AppImage'),
        env={**os.environ, 'ARCH': 'x86_64', 'APPIMAGE_EXTRACT_AND_RUN': '1'})


def deb():
    root = fresh(os.path.join(DIST, 'deb'))
    shutil.copytree(BUNDLE, os.path.join(root, 'opt', 'schematrix'))
    os.makedirs(os.path.join(root, 'usr', 'bin'))
    os.symlink('/opt/schematrix/Schematrix', os.path.join(root, 'usr', 'bin', 'schematrix'))
    write(os.path.join(root, 'usr', 'share', 'applications', 'schematrix.desktop'), DESKTOP.format(exec='schematrix'))
    doc = os.path.join(root, 'usr', 'share', 'doc', 'schematrix')
    os.makedirs(doc)
    shutil.copy(os.path.join(ROOT, 'LICENSE'), os.path.join(doc, 'copyright'))
    icon = os.path.join(root, 'usr', 'share', 'icons', 'hicolor', '256x256', 'apps')
    os.makedirs(icon)
    shutil.copy(os.path.join(PKG, 'schematrix.png'), icon)
    size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(root) for f in fs
               if not os.path.islink(os.path.join(d, f))) // 1024
    # the bundle carries its own Python; a Chromium browser gives the fastest window, GTK WebKit is the fallback
    write(os.path.join(root, 'DEBIAN', 'control'), f"""Package: schematrix
Version: {VERSION}
Architecture: amd64
Maintainer: Instrix <https://github.com/Instrix/Instrtix-Schematrix>
Installed-Size: {size}
Depends: libc6 (>= 2.35)
Recommends: chromium | chromium-browser | google-chrome-stable
Suggests: python3-gi, gir1.2-webkit2-4.1, ngspice
Section: electronics
Priority: optional
Homepage: https://github.com/Instrix/Instrtix-Schematrix
Description: Electrical schematic editor and Python scripting library
 Draw schematics with KiCad-style wiring, export SVG, PNG, PDF and TikZ for
 LaTeX, and exchange SPICE and KiCad netlists. Includes the Schematrix
 command line (schematrix --help).
""")
    run('dpkg-deb', '--root-owner-group', '-Zxz', '--build', root, os.path.join(OUT, 'schematrix_amd64.deb'))


# ---------------------------------------------------------------- Windows
def windows():
    with zipfile.ZipFile(os.path.join(OUT, 'Schematrix-windows.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
        for d, _, fs in os.walk(BUNDLE):
            for f in fs:
                p = os.path.join(d, f)
                z.write(p, os.path.join('Schematrix', os.path.relpath(p, BUNDLE)))
    iscc = shutil.which('iscc') or r'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'
    if not os.path.exists(iscc) and not shutil.which('iscc'):
        sys.exit('Inno Setup (ISCC) not found: install it to build Schematrix-Setup.exe')
    run(iscc, f'/DVersion={VERSION}', f'/DSource={BUNDLE}', f'/DOutDir={OUT}', os.path.join(PKG, 'schematrix.iss'))


# ---------------------------------------------------------------- macOS
def macos():
    app = os.path.join(DIST, 'Schematrix.app')
    stage = fresh(os.path.join(DIST, 'dmg'))
    shutil.copytree(app, os.path.join(stage, 'Schematrix.app'), symlinks=True)
    os.symlink('/Applications', os.path.join(stage, 'Applications'))       # drag-to-install
    run('hdiutil', 'create', '-volname', 'Schematrix', '-srcfolder', stage, '-ov', '-format', 'UDZO',
        os.path.join(OUT, 'Schematrix-macos.dmg'))


def main():
    os.makedirs(OUT, exist_ok=True)
    system = platform.system()
    if system == 'Linux':
        deb()
        appimage()
    elif system == 'Windows':
        windows()
    elif system == 'Darwin':
        macos()
    else:
        sys.exit(f'no packaging for {system}')
    for f in sorted(os.listdir(OUT)):
        print(f'{f}  {os.path.getsize(os.path.join(OUT, f)) / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
