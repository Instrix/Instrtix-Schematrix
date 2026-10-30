"""Runs a user script (or a legacy figure script) in a child process and reports the schematics it made.

The parent (server or CLI) sends {"mode": "script" | "legacy", "code": "...", "filename": "..."} on stdin and reads
one JSON object from the last line of stdout: {"ok", "docs": [{"name", "doc"}], "stdout", "error"}.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import traceback

RUNNER_FLAG = '--schematrix-runner'
SENTINEL = '\x1e@@SCHEMATRIX-RESULT@@'


def child_main():
    req = json.loads(sys.stdin.read())
    from . import document as D
    from .compat import import_legacy
    buf = io.StringIO()
    res = {'ok': True, 'docs': [], 'stdout': '', 'error': None}
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            from .compat import is_legacy
            if req.get('mode') == 'legacy' or is_legacy(req['code']):      # old S-class figure scripts import
                for name, sch in import_legacy(source=req['code'], filename=req.get('filename') or 'legacy.py'):
                    res['docs'].append({'name': name, 'doc': sch.doc})
            else:
                D.reset_registry()
                ns = {'__name__': '__main__', '__file__': req.get('filename') or 'script.py'}
                exec(compile(req['code'], req.get('filename') or 'script.py', 'exec'), ns)
                for i, s in enumerate(D.shown_or_created()):
                    if s.doc['elements']:
                        res['docs'].append({'name': s.title or f'schematic-{i + 1}', 'doc': s.doc})
    except BaseException as e:  # noqa: BLE001 - report everything, including SystemExit, to the user
        res['ok'] = False
        tbe = traceback.TracebackException.from_exception(e)
        tbe.stack = traceback.StackSummary.from_list(
            [f for f in tbe.stack if os.path.basename(f.filename) != 'runner.py'])
        res['error'] = f'{type(e).__name__}: {e}'
        res['traceback'] = ''.join(tbe.format())
    res['stdout'] = buf.getvalue()[-20000:]
    sys.stdout.write('\n' + SENTINEL + json.dumps(res, ensure_ascii=False, default=str) + '\n')
    sys.stdout.flush()


def _limits():  # POSIX only: keep a runaway script from eating the host
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (2 << 30, 2 << 30))
        resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    except Exception:  # noqa: BLE001
        pass


def run(code: str, mode='script', filename=None, timeout=30.0, cwd=None) -> dict:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if getattr(sys, 'frozen', False):
        cmd = [sys.executable, RUNNER_FLAG]
    else:
        boot = f'import sys; sys.path.insert(0, {root!r}); from schematrix.runner import child_main; child_main()'
        cmd = [sys.executable, '-I', '-c', boot]
    cwd = cwd or tempfile.gettempdir()
    try:
        p = subprocess.run(cmd, input=json.dumps({'mode': mode, 'code': code, 'filename': filename}),
                           capture_output=True, text=True, timeout=timeout, cwd=cwd, encoding='utf-8',
                           preexec_fn=_limits if os.name == 'posix' else None)
    except subprocess.TimeoutExpired:
        return {'ok': False, 'docs': [], 'stdout': '', 'error': f'script timed out after {timeout:g} s'}
    out = p.stdout or ''
    i = out.rfind(SENTINEL)
    if i < 0:
        return {'ok': False, 'docs': [], 'stdout': out[-20000:],
                'error': (p.stderr or 'script ended without a result (killed?)')[-4000:]}
    res = json.loads(out[i + len(SENTINEL):])
    pre = out[:i].rstrip('\n')
    if pre:
        res['stdout'] = pre + '\n' + res.get('stdout', '')
    if p.stderr:
        res['stdout'] = res.get('stdout', '') + p.stderr[-4000:]
    return res
