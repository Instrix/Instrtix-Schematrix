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


def cairo_svg(svg: str, theme=None) -> str:
    """an SVG ready for cairosvg: text in the bundled fonts as outlines (the same on every computer, whatever fonts
    it has), overbars and anchors fixed on the text that remains"""
    from .outline import outline
    return for_cairo(outline(svg), theme)


def for_cairo(svg: str, theme=None) -> str:
    """cairosvg ignores text-decoration and anchors every tspan on its own: measure the runs of each marked-up text
    with cairo itself (same engine, same first font family), left-anchor the text at its true start and draw each
    overbar as a line"""
    if '<tspan' not in svg:
        return svg
    import re
    import xml.etree.ElementTree as ET
    import cairocffi as cairo
    from . import symbols as SYM
    from . import theme as TH
    NS = 'http://www.w3.org/2000/svg'
    ET.register_namespace('', NS)
    root = ET.fromstring(svg)
    t = TH.resolve(theme)
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    first = lambda fam: fam.split(',')[0].strip('"\' ')

    def measure(text, family, size, bold, italic):
        ctx.select_font_face(family, cairo.FONT_SLANT_ITALIC if italic else cairo.FONT_SLANT_NORMAL,
                             cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(size)
        return ctx.text_extents(text)[4]
    for parent in root.iter():
        for idx, el in reversed(list(enumerate(list(parent)))):
            if el.tag != f'{{{NS}}}text' or not len(el):
                continue
            cls = (el.get('class') or 'lbl').split()[0]
            m = re.search(r'font-size:\s*([\d.]+)px', el.get('style') or '')
            fs = float(m.group(1)) if m else SYM.FONT_SIZES.get(cls, 12)
            family = first(t['sans'] if cls in ('note', 'title') else t['mono'])
            bold = int((t['strong'] if cls in ('pin', 'termlbl', 'accl', 'grplbl', 'title') else t['weight'])) >= 600
            italic = cls == 'node' or (cls in ('ref', 'accl') and t['ref_style'] == 'italic')
            color = t['accent'] if cls == 'accl' else t['muted'] if cls in ('val', 'valsm', 'grplbl', 'note') else t['text']
            runs, x, base = [], 0.0, 0.0
            def add(text, size, over):
                nonlocal x
                w = measure(text, family, size, bold, italic)
                runs.append((x, x + w, over)); x += w
            add(el.text or '', fs, False)
            for c in el:
                base += float(c.get('dy') or 0)
                st = c.get('style') or ''
                sm = re.search(r'font-size:\s*([\d.]+)px', st)
                add(c.text or '', float(sm.group(1)) if sm else fs, 'overline' in st)
                c.set('style', re.sub(r'text-decoration:overline;?', '', st).strip(';'))
                if not c.get('style'):
                    del c.attrib['style']
                add(c.tail or '', fs, False)
            x0 = float(el.get('x', 0)) - {'start': 0, 'middle': x / 2, 'end': x}[el.get('text-anchor', 'start')]
            el.set('x', f'{x0:.2f}'); el.set('text-anchor', 'start')
            y = float(el.get('y', 0)) - fs * 0.8
            for a, b, over in runs:
                if over and b > a:
                    parent.insert(idx + 1, ET.Element(f'{{{NS}}}line', {
                        'x1': f'{x0 + a + fs * 0.04:.2f}', 'x2': f'{x0 + b - fs * 0.04:.2f}', 'y1': f'{y:.2f}', 'y2': f'{y:.2f}',
                        'stroke': color, 'stroke-width': f'{max(0.6, fs * 0.065):.2f}'}))
    return ET.tostring(root, encoding='unicode')


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
    svg = cairo_svg(svg, doc.get('theme'))
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
