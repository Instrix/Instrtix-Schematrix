"""Exporting drawings: every format behind one call, for the whole sheet or only some elements.

    data, mime, ext = export(doc, 'png', ids=['e3', 'e4'], background='none', scale=3)

Formats: svg, png, jpeg, webp, pdf, eps, tikz (picture code) and tikz-standalone (a compilable .tex). PNG, PDF
and EPS need cairosvg; JPEG and WebP also need Pillow (the editor can make bitmaps in the browser without either).
"""
from __future__ import annotations

import copy
import io

from . import render as R

FORMATS = {
    'svg': ('image/svg+xml', 'svg'), 'png': ('image/png', 'png'), 'jpeg': ('image/jpeg', 'jpg'),
    'webp': ('image/webp', 'webp'), 'pdf': ('application/pdf', 'pdf'), 'eps': ('application/postscript', 'eps'),
    'tikz': ('text/x-tex', 'tikz'), 'tikz-standalone': ('text/x-tex', 'tex'),
}
ALIASES = {'jpg': 'jpeg', 'tex': 'tikz-standalone', 'ps': 'eps'}
OPAQUE = {'jpeg'}            # formats without transparency: a transparent background becomes the theme paper


class ExportError(RuntimeError):
    pass


def subset(doc, ids=None, margin=None) -> dict:
    """the document cropped to some elements (or to its drawing) with a margin; ids None = everything"""
    d = copy.deepcopy(doc)
    if ids is not None:
        keep = set(ids)
        d['elements'] = [e for e in d['elements'] if e.get('id') in keep]
        if not d['elements']:
            raise ExportError('nothing selected to export')
    pg = d.setdefault('page', {})
    if ids is not None or margin is not None:
        pg['auto'] = True
        if margin is not None:
            pg['margin'] = margin
    return d


def svg_of(doc, background=True, fonts=True, ids=None, margin=None) -> str:
    return R.render_svg(subset(doc, ids, margin), embed_fonts=fonts, background=background)


def export(doc, fmt='svg', *, ids=None, background=True, scale=2.0, margin=None, fonts=True, quality=92):
    """-> (bytes, mime type, file extension). background: True (theme paper), False / 'none', or a colour."""
    fmt = ALIASES.get(fmt, fmt)
    if fmt not in FORMATS:
        raise ExportError(f'unknown format {fmt!r}; one of {", ".join(FORMATS)}')
    mime, ext = FORMATS[fmt]
    if fmt in OPAQUE and background in (False, None, 'none', 'transparent'):
        background = True
    if fmt.startswith('tikz'):
        from . import tikz
        d = subset(doc, ids, margin)
        return tikz.to_tikz(d, background=background, standalone=fmt == 'tikz-standalone').encode(), mime, ext
    svg = svg_of(doc, background, fonts and fmt == 'svg', ids, margin)
    if fmt == 'svg':
        return svg.encode(), mime, ext
    try:
        import cairosvg
    except Exception as e:  # noqa: BLE001
        raise ExportError(f'{fmt.upper()} export needs cairosvg on the server (pip install cairosvg): {e}') from None
    if fmt == 'pdf':
        return cairosvg.svg2pdf(bytestring=svg.encode()), mime, ext
    if fmt == 'eps':
        return cairosvg.svg2eps(bytestring=svg.encode()), mime, ext
    png = cairosvg.svg2png(bytestring=svg.encode(), scale=scale)
    if fmt == 'png':
        return png, mime, ext
    try:
        from PIL import Image
    except Exception:  # noqa: BLE001
        raise ExportError(f'{fmt.upper()} export needs Pillow on the server (pip install pillow)') from None
    im = Image.open(io.BytesIO(png))
    if fmt == 'jpeg':
        im = im.convert('RGB')
    out = io.BytesIO()
    im.save(out, 'JPEG' if fmt == 'jpeg' else 'WEBP', quality=quality)
    return out.getvalue(), mime, ext
