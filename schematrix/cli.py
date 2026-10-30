"""Command line: `schematrix app` (native window), `schematrix serve` (web), plus render/run/netlist/import tools."""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

from .runner import RUNNER_FLAG


APP_PORT = 47815      # fixed so the editor's browser storage (autosave, settings) survives restarts


def _free_port(prefer=None):
    for p in ([prefer] if prefer else []) + [0]:
        with socket.socket() as s:
            try:
                s.bind(('127.0.0.1', p))
                return s.getsockname()[1]
            except OSError:
                continue


def _schematrix_at(port) -> bool:
    """is a Schematrix server already answering on this port?"""
    import urllib.request
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health', timeout=0.5) as r:
            return b'"ok"' in r.read()
    except Exception:  # noqa: BLE001
        return False


def _chromium():
    """a Chromium-family browser that can open an app window, or None"""
    import shutil
    for exe in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable', 'brave-browser',
                'microsoft-edge', 'microsoft-edge-stable', 'vivaldi'):
        path = shutil.which(exe)
        if path:
            return path
    return None


def _chromium_window(exe, url):
    """open url as a standalone app window (no tabs or address bar) with its own profile; returns the process"""
    import subprocess
    profile = Path(os.environ.get('XDG_CACHE_HOME') or Path.home() / '.cache') / 'schematrix' / 'chromium-profile'
    profile.mkdir(parents=True, exist_ok=True)
    return subprocess.Popen([exe, f'--app={url}', f'--user-data-dir={profile}', '--no-first-run', '--no-default-browser-check',
                             '--window-size=1440,900', '--class=Schematrix'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _serve(host, port, workspace=None, log='info'):
    if workspace:
        os.environ['SCHEMATRIX_WORKSPACE'] = str(Path(workspace).expanduser().resolve())
    import uvicorn
    from .server import create_app
    uvicorn.run(create_app(), host=host, port=port, log_level=log)


def cmd_serve(a):
    url = f'http://{"localhost" if a.host in ("0.0.0.0", "::") else a.host}:{a.port}/'
    print(f'Schematrix on {url}  (workspace: {a.workspace or os.environ.get("SCHEMATRIX_WORKSPACE") or Path.home() / "Schematrix"})')
    if a.open:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    _serve(a.host, a.port, a.workspace)


def cmd_app(a):
    """local server + an app window: Chromium app mode (fastest on Linux) or pywebview, else the default browser"""
    engine = a.engine or os.environ.get('SCHEMATRIX_ENGINE') or 'auto'
    if a.browser:
        engine = 'browser'
    if engine == 'auto':
        engine = 'chromium' if sys.platform.startswith('linux') and _chromium() else 'webview'
    if not a.port and not a.workspace and _schematrix_at(APP_PORT):     # already running: just open another window
        url = f'http://127.0.0.1:{APP_PORT}/'
        if engine == 'chromium' and _chromium():
            _chromium_window(_chromium(), url)
        else:
            webbrowser.open(url)
        return
    port = a.port or _free_port(APP_PORT)
    t = threading.Thread(target=_serve, args=('127.0.0.1', port, a.workspace, 'warning'), daemon=True)
    t.start()
    url = f'http://127.0.0.1:{port}/'
    t0 = time.monotonic()
    for _ in range(100):
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.05)
    why = 'asked for the browser' if engine == 'browser' else None
    if engine == 'chromium':
        exe = _chromium()
        if exe:
            proc = _chromium_window(exe, url)
            try:
                proc.wait()
                if time.monotonic() - t0 < 3:      # the browser handed the window to a running instance: keep serving
                    t.join()
            except KeyboardInterrupt:
                pass
            return
        why = 'no Chromium / Chrome found for the app window'
    if not why:
        try:
            import webview  # pywebview
        except ImportError:
            why = 'pywebview is not installed (install the "desktop" extra for a native window)'
    if not why:
        gui = _gui_backend()
        if gui is False:
            why = ('no GUI toolkit for a native window. Either install GTK bindings and reinstall with '
                   '"pipx install --system-site-packages ..." (Debian/Ubuntu: sudo apt install python3-gi gir1.2-webkit2-4.1), '
                   'or add Qt: "pipx inject schematrix qtpy pyqt6 pyqt6-webengine"')
        else:
            try:
                webview.create_window('Schematrix', url, width=1440, height=900, min_size=(900, 600))
                webview.start(gui=gui)
                return
            except Exception as e:  # noqa: BLE001  (any toolkit failure: fall back to the browser)
                why = f'the native window failed ({e})'
    print(f'Schematrix running at {url} in your browser: {why}. Ctrl+C to quit.')
    webbrowser.open(url)
    try:
        t.join()
    except KeyboardInterrupt:
        pass


def _borrow_system_gi():
    """pipx / venv installs can't see the distribution's GTK bindings (python3-gi); append the system
    site-packages that hold them to the end of sys.path, so they never shadow the venv's own packages"""
    v = f'python{sys.version_info.major}.{sys.version_info.minor}'
    for d in ('/usr/lib/python3/dist-packages', f'/usr/lib/{v}/site-packages', f'/usr/lib64/{v}/site-packages',
              f'/usr/local/lib/{v}/dist-packages'):
        if os.path.isdir(os.path.join(d, 'gi')) and d not in sys.path:
            sys.path.append(d)
            return


def _gui_backend():
    """the pywebview GUI to use: None (platform default), 'gtk' or 'qt'; False if Linux has neither"""
    if not sys.platform.startswith('linux'):
        return None                     # Windows (Edge WebView2) and macOS (Cocoa) are built in
    import importlib.util
    if not importlib.util.find_spec('gi'):
        _borrow_system_gi()
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk  # noqa: F401
        for wk in ('4.1', '4.0'):
            try:
                gi.require_version('WebKit2', wk)
                from gi.repository import WebKit2  # noqa: F401
                return 'gtk'
            except (ValueError, ImportError):
                continue
    except Exception:  # noqa: BLE001  (missing or broken bindings: try Qt)
        pass
    try:
        import qtpy  # noqa: F401
        from qtpy import QtWebEngineWidgets  # noqa: F401
        return 'qt'
    except Exception:  # noqa: BLE001
        return False


def _load_any(path):
    """a .json document -> [(name, doc)]; a .py script -> the schematics it makes"""
    from . import document as D
    from . import runner
    p = Path(path)
    if p.suffix == '.json':
        with open(p, encoding='utf-8') as f:
            return [(p.stem, D.normalize(json.load(f)))]
    res = runner.run(p.read_text(encoding='utf-8'), 'script', str(p), timeout=120, cwd=str(p.parent.resolve()))
    if res.get('stdout'):
        print(res['stdout'], end='' if res['stdout'].endswith('\n') else '\n')
    if not res['ok']:
        sys.exit(res.get('traceback') or res['error'])
    return [(d['name'], d['doc']) for d in res['docs']]


def _write(doc, out: Path, fmt, fonts):
    from . import export as EX
    from . import netlist as NET
    out.parent.mkdir(parents=True, exist_ok=True)
    if fmt in ('png', 'jpg', 'jpeg', 'webp', 'pdf', 'eps', 'tikz', 'tex', 'svg') and getattr(_write, 'opts', None):
        out.write_bytes(EX.export(doc, fmt, **_write.opts)[0])
    elif fmt == 'json':
        out.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding='utf-8')
    elif fmt in ('svg', 'png', 'jpg', 'jpeg', 'webp', 'pdf', 'eps', 'tikz', 'tex'):
        out.write_bytes(EX.export(doc, fmt, fonts=fonts)[0])
    elif fmt in ('cir', 'spice'):
        out.write_text(NET.to_spice(doc), encoding='utf-8')
    elif fmt == 'net':
        from . import netio
        out.write_text(netio.export(doc, 'kicad'), encoding='utf-8')
    else:
        sys.exit(f'unknown format {fmt}')
    print('wrote', out)


def _slug(s):
    import re
    return re.sub(r'[^\w\-]+', '-', s).strip('-') or 'schematic'


def cmd_render(a):
    bg = {'paper': True, 'none': False, 'transparent': False}.get(a.background, a.background)
    _write.opts = {'fonts': a.fonts, 'background': bg, 'scale': a.scale, 'margin': a.margin}
    docs = _load_any(a.input)
    fmts = a.format.split(',')
    if a.output and len(docs) == 1 and Path(a.output).suffix:
        _write(docs[0][1], Path(a.output), Path(a.output).suffix[1:], a.fonts)
        return
    outdir = Path(a.output or '.')
    for name, doc in docs:
        for f in fmts:
            _write(doc, outdir / f'{_slug(name)}.{f}', f, a.fonts)


def cmd_netlist(a):
    from . import netio
    for name, doc in _load_any(a.input):
        text = netio.export(doc, a.format)
        if a.output:
            Path(a.output).write_text(text, encoding='utf-8'); print('wrote', a.output)
        else:
            print(text, end='')


def cmd_import_netlist(a):
    from . import netio
    text = Path(a.input).read_text(encoding='utf-8')
    sch = netio.import_netlist(text, a.netformat, a.input)
    for w in sch.warnings:
        print('warning:', w, file=sys.stderr)
    out = Path(a.output or Path(a.input).with_suffix('.json').name)
    for f in a.format.split(','):
        _write(sch.doc, out.with_suffix('.' + f), f, a.fonts)


def cmd_import(a):
    from .compat import import_legacy
    outdir = Path(a.output)
    for name, sch in import_legacy(a.input):
        for f in a.format.split(','):
            _write(sch.doc, outdir / f'{_slug(name)}.{f}', f, a.fonts)


def cmd_symbols(a):
    from . import symbols as SYM
    for e in SYM.catalog():
        props = ', '.join(k for k in e['props'] if k not in ('ref', 'value', 'part'))
        pins = ', '.join(e['geometry']['pins'])
        print(f'{e["name"]:14s} {e["title"]:18s} pins: {pins:26s} props: {props}')


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == [RUNNER_FLAG]:           # frozen builds run scripts by re-invoking themselves
        from .runner import child_main
        return child_main()
    ap = argparse.ArgumentParser(prog='schematrix', description='Electrical schematics: editor, renderer and scripting.')
    sub = ap.add_subparsers(dest='cmd')
    s = sub.add_parser('app', help='open the editor in a native window (default)')
    s.add_argument('--port', type=int); s.add_argument('--workspace'); s.add_argument('--browser', action='store_true', help='use the web browser instead')
    s.add_argument('--engine', choices=['auto', 'chromium', 'webview', 'browser'],
                   help='window: chromium (app mode, default on Linux when installed), webview (pywebview), browser')
    s.set_defaults(fn=cmd_app)
    s = sub.add_parser('serve', help='run the web server')
    s.add_argument('--host', default=os.environ.get('SCHEMATRIX_HOST', '127.0.0.1'))
    s.add_argument('--port', type=int, default=int(os.environ.get('SCHEMATRIX_PORT', 8000)))
    s.add_argument('--workspace'); s.add_argument('--open', action='store_true', help='open a browser')
    s.set_defaults(fn=cmd_serve)
    s = sub.add_parser('render', help='render a .json document or a .py script to svg/png/pdf/json/cir')
    s.add_argument('input'); s.add_argument('-o', '--output', help='file (single result) or folder')
    s.add_argument('-f', '--format', default='svg', help='comma list: svg,png,jpg,webp,pdf,eps,tikz,tex,json,cir (SPICE),net (KiCad netlist)')
    s.add_argument('--fonts', action='store_true', help='embed the fonts in SVGs (portable, ~200 kB)')
    s.add_argument('--background', default='paper', help='paper (theme), none / transparent, or a colour like "#fff"')
    s.add_argument('--scale', type=float, default=2.0, help='bitmap scale (2 = 192 dpi)')
    s.add_argument('--margin', type=float, help='crop margin around the drawing')
    s.set_defaults(fn=cmd_render)
    s = sub.add_parser('netlist', help='write the netlist of a document or script (SPICE, KiCad .net or JSON)')
    s.add_argument('input'); s.add_argument('-f', '--format', default='spice', choices=['spice', 'kicad', 'json'])
    s.add_argument('-o', '--output', help='file (default: print)'); s.set_defaults(fn=cmd_netlist)
    s = sub.add_parser('import-netlist', help='draw a schematic from a netlist (SPICE, KiCad .net or Schematrix JSON)')
    s.add_argument('input'); s.add_argument('-o', '--output', help='output file stem (default: input name)')
    s.add_argument('--netformat', choices=['spice', 'kicad', 'json'], help='input format (default: detect)')
    s.add_argument('-f', '--format', default='json,svg', help='comma list: json,svg,png,pdf')
    s.add_argument('--fonts', action='store_true'); s.set_defaults(fn=cmd_import_netlist)
    s = sub.add_parser('import-legacy', help='convert a legacy S-class figure script into documents')
    s.add_argument('input'); s.add_argument('-o', '--output', default='.'); s.add_argument('-f', '--format', default='json,svg')
    s.add_argument('--fonts', action='store_true'); s.set_defaults(fn=cmd_import)
    s = sub.add_parser('symbols', help='list the symbol library'); s.set_defaults(fn=cmd_symbols)
    a = ap.parse_args(argv)
    if not getattr(a, 'fn', None):
        a = ap.parse_args(['app'] + argv)
    a.fn(a)


if __name__ == '__main__':
    main()
