"""HTTP API + the web editor.

Environment:
    SCHEMATRIX_WORKSPACE   folder for saved documents and scripts (default ~/Schematrix, /data in Docker)
    SCHEMATRIX_SCRIPTS     1 (default) lets the editor run Python scripts on the server; set 0 on a shared deployment
    SCHEMATRIX_TOKEN       if set, every API call needs it (header "Authorization: Bearer <token>" or the cookie
                         set by visiting /?token=<token>)
    SCHEMATRIX_SCRIPT_TIMEOUT  seconds per script run (default 30)
"""
from __future__ import annotations

import datetime as dt
import hmac
import os
import re
import shutil
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles

from . import __version__
from . import document as D
from . import export as EX
from . import netio
from . import netlist as NET
from . import render as R
from . import runner
from . import symbols as SYM
from . import theme as TH

WEB = Path(__file__).parent / 'web'
ALLOWED_EXT = {'.json', '.py', '.svg', '.cir', '.sp', '.net', '.tikz', '.tex'}


def _truthy(v, default=True):
    if v is None:
        return default
    return str(v).strip().lower() not in ('0', 'false', 'no', 'off', '')


EXAMPLES = Path(__file__).parent / 'examples'


def workspace() -> Path:
    p = Path(os.environ.get('SCHEMATRIX_WORKSPACE') or (Path.home() / 'Schematrix')).expanduser()
    p.mkdir(parents=True, exist_ok=True)
    _seed_examples(p)
    return p


def _seed_examples(ws: Path):
    """copy example files into ws/examples that this workspace has never received (a new version brings new
    examples); files already given once are never copied again, so edits and deletions stick"""
    record = ws / 'examples' / '.seeded'
    try:
        seeded = set(record.read_text(encoding='utf-8').split('\n')) if record.exists() else set()
        added = []
        for src in EXAMPLES.rglob('*'):
            if not src.is_file() or '__pycache__' in src.parts:
                continue
            rel = src.relative_to(EXAMPLES).as_posix()
            if rel in seeded:
                continue
            dst = ws / 'examples' / rel
            if not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            added.append(rel)
        if added:
            record.parent.mkdir(parents=True, exist_ok=True)
            record.write_text('\n'.join(sorted(seeded | set(added))), encoding='utf-8')
    except OSError:
        pass                                        # a read-only workspace still works, just without new examples


def safe_path(rel: str) -> Path:
    rel = rel.replace('\\', '/').strip('/')
    if not rel or any(part in ('', '.', '..') for part in rel.split('/')) or not re.fullmatch(r'[\w\-. /]+', rel):
        raise HTTPException(400, 'bad file name')
    p = (workspace() / rel).resolve()
    if workspace().resolve() not in p.parents:
        raise HTTPException(400, 'outside the workspace')
    if p.suffix.lower() not in ALLOWED_EXT:
        raise HTTPException(400, f'only {", ".join(sorted(ALLOWED_EXT))} files')
    return p


def _has(mod):
    import importlib.util
    return importlib.util.find_spec(mod) is not None


def pdf_available():
    try:
        import cairosvg  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


def create_app() -> FastAPI:
    app = FastAPI(title='Schematrix', version=__version__, docs_url='/api/docs', redoc_url=None)
    token = os.environ.get('SCHEMATRIX_TOKEN') or None

    @app.middleware('http')
    async def auth(request: Request, call_next):
        if token:
            path = request.url.path
            q = request.query_params.get('token')
            if q and hmac.compare_digest(q, token):
                resp = await call_next(request)
                resp.set_cookie('schematrix_token', token, httponly=True, samesite='strict')
                return resp
            given = request.cookies.get('schematrix_token') or request.headers.get('authorization', '').removeprefix('Bearer ').strip()
            if not (given and hmac.compare_digest(given, token)) and path != '/api/health':
                if path.startswith('/api/'):
                    return JSONResponse({'detail': 'token required'}, 401)
                return HTMLResponse('<p style="font-family:sans-serif">Schematrix: open this page with <code>?token=…</code></p>', 401)
        return await call_next(request)

    @app.get('/api/health')
    def health():
        return {'ok': True}

    @app.get('/api/info')
    def info():
        return {'version': __version__, 'pdf': pdf_available(), 'scripts': _truthy(os.environ.get('SCHEMATRIX_SCRIPTS')),
                'workspace': str(workspace()), 'themes': {k: v for k, v in TH.THEMES.items()},
                'text_classes': TH.TEXT_CLASSES, 'css': {k: TH.css(k) for k in TH.THEMES},
                'netlist_formats': netio.info(), 'pillow': _has('PIL')}

    @app.get('/api/symbols')
    def symbols():
        return SYM.catalog()

    @app.post('/api/geometry')
    def geometry(body: dict = Body(...)):
        out = []
        for it in body.get('items', []):
            try:
                out.append(SYM.get(it['sym']).geometry(it.get('props') or {}))
            except Exception as e:  # noqa: BLE001
                out.append({'error': str(e)})
        return out

    def _doc(body):
        try:
            return D.normalize(body['doc'] if 'doc' in body else body)
        except Exception as e:  # noqa: BLE001
            raise HTTPException(400, f'bad document: {e}')

    @app.post('/api/render')
    def render(body: dict = Body(...), format: str = 'svg', fonts: bool = True, scale: float = 2.0):
        doc = _doc(body)
        name = re.sub(r'[^\w\-]+', '-', doc.get('meta', {}).get('title') or 'schematic').strip('-') or 'schematic'
        if format == 'svg':
            return Response(R.render_svg(doc, embed_fonts=fonts), media_type='image/svg+xml',
                            headers={'Content-Disposition': f'inline; filename="{name}.svg"'})
        if format == 'spice':
            return PlainTextResponse(NET.to_spice(doc), headers={'Content-Disposition': f'attachment; filename="{name}.cir"'})
        if format in ('png', 'pdf'):
            if not pdf_available():
                raise HTTPException(501, 'PNG/PDF export needs cairosvg on the server (pip install cairosvg)')
            svg = R.render_svg(doc)
            data = R.to_png(svg, scale) if format == 'png' else R.to_pdf(svg)
            return Response(data, media_type='image/png' if format == 'png' else 'application/pdf',
                            headers={'Content-Disposition': f'attachment; filename="{name}.{format}"'})
        raise HTTPException(400, 'format must be svg, png, pdf or spice')

    @app.post('/api/export')
    def export(body: dict = Body(...)):
        """body: {doc, format: svg|png|jpeg|webp|pdf|eps|tikz|tikz-standalone, ids?: [element ids to export, cropped],
        background?: true (theme paper) | false (transparent) | '#rrggbb', scale?: 2, margin?: 20, fonts?: true}"""
        doc = _doc(body)
        try:
            data, mime, ext = EX.export(doc, body.get('format', 'svg'), ids=body.get('ids'), background=body.get('background', True),
                                        scale=float(body.get('scale', 2)), margin=body.get('margin'), fonts=body.get('fonts', True))
        except EX.ExportError as e:
            raise HTTPException(501 if 'needs' in str(e) else 400, str(e))
        name = re.sub(r'[^\w\-]+', '-', body.get('name') or doc.get('meta', {}).get('title') or 'schematic').strip('-') or 'schematic'
        return Response(data, media_type=mime, headers={'Content-Disposition': f'attachment; filename="{name}.{ext}"'})

    @app.post('/api/netlist')
    def netlist(body: dict = Body(...)):
        doc = _doc(body)
        nx = NET.extract(doc)
        return {'nets': nx['nets'], 'warnings': nx['warnings'], 'spice': NET.to_spice(doc),
                'pins': [[k[0], k[1], v] for k, v in nx['pins'].items()]}

    @app.post('/api/netlist/export')
    def netlist_export(body: dict = Body(...), format: str = 'spice'):
        """the document's netlist as a file: format = spice | kicad | json"""
        if format not in netio.FORMATS:
            raise HTTPException(400, f'format must be one of {", ".join(netio.FORMATS)}')
        doc = _doc(body)
        name = re.sub(r'[^\w\-]+', '-', doc.get('meta', {}).get('title') or 'schematic').strip('-') or 'schematic'
        return Response(netio.export(doc, format), media_type=netio.FORMATS[format]['mime'],
                        headers={'Content-Disposition': f'attachment; filename="{name}{netio.EXT[format]}"'})

    @app.post('/api/netlist/import')
    def netlist_import(body: dict = Body(...)):
        """netlist text -> a new document. body: {text, format?: spice|kicad|json, filename?, title?}"""
        text = body.get('text') or ''
        if not text.strip():
            raise HTTPException(400, 'empty netlist')
        fmt = body.get('format') or netio.detect(text, body.get('filename') or '')
        try:
            sch = netio.import_netlist(text, fmt, body.get('filename') or '', body.get('title'))
        except Exception as e:  # noqa: BLE001
            raise HTTPException(400, f'could not read the {fmt} netlist: {e}')
        return {'format': fmt, 'doc': sch.doc, 'warnings': sch.warnings}

    def _run(code, mode, filename):
        if not _truthy(os.environ.get('SCHEMATRIX_SCRIPTS')):
            raise HTTPException(403, 'script execution is disabled on this server (SCHEMATRIX_SCRIPTS=0)')
        return runner.run(code, mode, filename, float(os.environ.get('SCHEMATRIX_SCRIPT_TIMEOUT', 30)), cwd=str(workspace()))

    @app.post('/api/run')
    def run(body: dict = Body(...)):
        return _run(body.get('code', ''), 'script', body.get('filename') or 'script.py')

    @app.post('/api/import-legacy')
    def import_legacy(body: dict = Body(...)):
        return _run(body.get('code', ''), 'legacy', body.get('filename') or 'legacy.py')

    @app.get('/api/files')
    def files():
        ws = workspace()
        out = []
        for p in sorted(ws.rglob('*')):
            if p.is_file() and p.suffix.lower() in ALLOWED_EXT and not any(s.startswith('.') for s in p.relative_to(ws).parts):
                st = p.stat()
                out.append({'path': p.relative_to(ws).as_posix(), 'size': st.st_size,
                            'modified': dt.datetime.fromtimestamp(st.st_mtime).isoformat(timespec='seconds')})
        return out

    @app.get('/api/files/{path:path}')
    def read_file(path: str):
        p = safe_path(path)
        if not p.exists():
            raise HTTPException(404, 'no such file')
        return FileResponse(p)

    @app.put('/api/files/{path:path}')
    async def write_file(path: str, request: Request):
        p = safe_path(path)
        data = await request.body()
        if len(data) > 20 << 20:
            raise HTTPException(413, 'too large')
        if p.suffix == '.json':
            import json
            try:
                D.normalize(json.loads(data))
            except Exception as e:  # noqa: BLE001
                raise HTTPException(400, f'not a Schematrix document: {e}')
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + '.tmp')
        tmp.write_bytes(data)
        os.replace(tmp, p)
        return {'ok': True, 'path': p.relative_to(workspace()).as_posix()}

    @app.delete('/api/files/{path:path}')
    def delete_file(path: str):
        p = safe_path(path)
        if p.exists():
            p.unlink()
        return {'ok': True}

    app.mount('/static', StaticFiles(directory=WEB), name='static')

    @app.get('/')
    def index():
        return FileResponse(WEB / 'index.html', headers={'Cache-Control': 'no-cache'})

    return app


app = create_app()
