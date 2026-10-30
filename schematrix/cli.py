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


def _free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


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
    """local server on a free port + a native window (pywebview), falling back to the default browser"""
    port = a.port or _free_port()
    t = threading.Thread(target=_serve, args=('127.0.0.1', port, a.workspace, 'warning'), daemon=True)
    t.start()
    url = f'http://127.0.0.1:{port}/'
    for _ in range(100):
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.05)
    try:
        if a.browser:
            raise ImportError
        import webview  # pywebview
        webview.create_window('Schematrix', url, width=1440, height=900, min_size=(900, 600))
        webview.start()
    except ImportError:
        print(f'Schematrix running at {url} (install pywebview for a native window). Ctrl+C to quit.')
        webbrowser.open(url)
        try:
            t.join()
        except KeyboardInterrupt:
            pass


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
    from . import netlist as NET
    from . import render as R
    out.parent.mkdir(parents=True, exist_ok=True)
    if fmt == 'json':
        out.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding='utf-8')
    elif fmt == 'svg':
        out.write_text(R.render_svg(doc, embed_fonts=fonts), encoding='utf-8')
    elif fmt == 'png':
        out.write_bytes(R.to_png(R.render_svg(doc)))
    elif fmt == 'pdf':
        out.write_bytes(R.to_pdf(R.render_svg(doc)))
    elif fmt in ('cir', 'spice', 'net'):
        out.write_text(NET.to_spice(doc), encoding='utf-8')
    else:
        sys.exit(f'unknown format {fmt}')
    print('wrote', out)


def _slug(s):
    import re
    return re.sub(r'[^\w\-]+', '-', s).strip('-') or 'schematic'


def cmd_render(a):
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
    from . import netlist as NET
    for name, doc in _load_any(a.input):
        print(NET.to_spice(doc), end='')


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
    s.set_defaults(fn=cmd_app)
    s = sub.add_parser('serve', help='run the web server')
    s.add_argument('--host', default=os.environ.get('SCHEMATRIX_HOST', '127.0.0.1'))
    s.add_argument('--port', type=int, default=int(os.environ.get('SCHEMATRIX_PORT', 8000)))
    s.add_argument('--workspace'); s.add_argument('--open', action='store_true', help='open a browser')
    s.set_defaults(fn=cmd_serve)
    s = sub.add_parser('render', help='render a .json document or a .py script to svg/png/pdf/json/cir')
    s.add_argument('input'); s.add_argument('-o', '--output', help='file (single result) or folder')
    s.add_argument('-f', '--format', default='svg', help='comma list: svg,png,pdf,json,cir')
    s.add_argument('--fonts', action='store_true', help='embed the fonts in SVGs (portable, ~200 kB)')
    s.set_defaults(fn=cmd_render)
    s = sub.add_parser('netlist', help='print a SPICE netlist'); s.add_argument('input'); s.set_defaults(fn=cmd_netlist)
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
