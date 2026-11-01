"""Public mode (SCHEMATRIX_PUBLIC=1): an instance anyone may use anonymously, without accounts or tokens.

Safety comes from what the server will not do, not from who is asking:
- no code execution: scripts and legacy-script import are off, whatever SCHEMATRIX_SCRIPTS says;
- no shared storage: nothing is written on the server; the bundled examples are served read-only and people keep
  their sheets in their own browser (Save downloads a file);
- no shared symbol library: custom symbols cannot be saved, and documents' embedded symbols are not adopted (they
  would change what other visitors see);
- bounded work: request size, document size, export scale / pixels, per-client request rates and the number of
  exports running at once are all capped;
- output hardening: raw SVG inside documents is stripped of scripts, exported files are served with a sandboxing
  CSP, the app page gets a strict CSP.

Limits can be tuned with SCHEMATRIX_PUBLIC_* variables (see LIMITS).
"""
from __future__ import annotations

import os
import re
import threading
import time
from collections import defaultdict, deque


def _env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


LIMITS = {
    'max_body': _env_int('SCHEMATRIX_PUBLIC_MAX_BODY', 4 << 20),            # bytes per request
    'max_elements': _env_int('SCHEMATRIX_PUBLIC_MAX_ELEMENTS', 4000),       # elements per document
    'max_scale': _env_int('SCHEMATRIX_PUBLIC_MAX_SCALE', 4),               # bitmap export scale
    'max_pixels': _env_int('SCHEMATRIX_PUBLIC_MAX_PIXELS', 40_000_000),     # bitmap export size
    'rate': _env_int('SCHEMATRIX_PUBLIC_RATE', 240),                       # requests per minute per client
    'heavy_rate': _env_int('SCHEMATRIX_PUBLIC_HEAVY_RATE', 30),            # exports / imports per minute per client
    'heavy_parallel': _env_int('SCHEMATRIX_PUBLIC_PARALLEL', 2),            # exports running at once, server-wide
}
HEAVY = ('/api/render', '/api/export', '/api/netlist/import', '/api/netlist/export', '/api/route')


def enabled() -> bool:
    return str(os.environ.get('SCHEMATRIX_PUBLIC', '')).strip().lower() in ('1', 'true', 'yes', 'on')


class RateLimiter:
    """sliding one-minute windows per client and bucket"""

    def __init__(self):
        self.hits = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, key, limit, window=60.0) -> float:
        """0 if allowed, else seconds to wait"""
        now = time.monotonic()
        with self.lock:
            q = self.hits[key]
            while q and q[0] <= now - window:
                q.popleft()
            if len(q) >= limit:
                return max(1.0, window - (now - q[0]))
            q.append(now)
            if len(self.hits) > 50_000:                 # forget idle clients
                for k in [k for k, v in self.hits.items() if not v or v[-1] <= now - window][:25_000]:
                    del self.hits[k]
            return 0.0


heavy_slots = threading.BoundedSemaphore(max(1, LIMITS['heavy_parallel']))


def client_ip(request) -> str:
    """the caller's address; behind a reverse proxy set SCHEMATRIX_TRUST_PROXY=1 to use the address it reports
    (the right-most X-Forwarded-For entry, the one the proxy itself appended)"""
    if os.environ.get('SCHEMATRIX_TRUST_PROXY', '').strip() in ('1', 'true', 'yes'):
        xff = request.headers.get('x-forwarded-for', '')
        if xff:
            return xff.split(',')[-1].strip()
    return request.client.host if request.client else '?'


_SCRIPT = re.compile(r'<\s*(script|foreignObject|iframe|object|embed)\b.*?(</\s*\1\s*>|/>)', re.I | re.S)
_ON = re.compile(r'\s+on[a-z]+\s*=\s*("[^"]*"|\'[^\']*\'|[^\s>]+)', re.I)
_JS = re.compile(r'(href|xlink:href|src)\s*=\s*("|\')\s*(javascript|data:text/html)[^"\']*\2', re.I)


def clean_svg(svg: str) -> str:
    """strip what could run code from raw SVG markup kept in a document"""
    svg = _SCRIPT.sub('', str(svg))
    svg = _ON.sub('', svg)
    return _JS.sub(r'\1=\2#\2', svg)


def check_doc(doc: dict):
    """size limits and sanitising for a document coming from an anonymous client; raises ValueError"""
    els = doc.get('elements') or []
    if len(els) > LIMITS['max_elements']:
        raise ValueError(f'documents on this public server are limited to {LIMITS["max_elements"]} elements')
    if doc.get('symbols'):
        raise ValueError('custom symbols are not available on this public server; use the desktop app or a self-hosted server')
    for e in els:
        if e.get('type') == 'raw':
            e['svg'] = clean_svg(e.get('svg', ''))
    return doc


def check_scale(scale: float, page_w: float, page_h: float) -> float:
    scale = max(0.25, min(float(scale), LIMITS['max_scale']))
    if page_w * page_h * scale * scale > LIMITS['max_pixels']:
        raise ValueError('that bitmap would be too large for this public server; lower the scale or export SVG / PDF')
    return scale


# a sandboxed response cannot run scripts even if someone opens an exported SVG straight from the server
EXPORT_CSP = "sandbox; default-src 'none'; style-src 'unsafe-inline'; font-src data:; img-src data:"
APP_CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
           "font-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
