"""Document JSON -> standalone SVG in the house style (the same markup the original figure scripts produced)."""
from __future__ import annotations

import math
from xml.sax.saxutils import escape

from . import geometry as GEO
from . import markup as MU
from . import symbols as SYM
from . import theme as TH


def esc(s):
    return escape(str(s), {'"': '&quot;'})


def num(v):
    v = round(float(v), 2)
    return str(int(v)) if v == int(v) else str(v)


def style_cls(base: str, style: str) -> str:
    toks = base.split()
    st = (style or '').split()
    if not st:
        return base
    if 'w' in toks:
        toks += [s for s in st if s not in toks]
    elif toks and toks[0] in ('amp', 'arrow', 'dot') and 'acc' in st:
        toks.append('acc')
    return ' '.join(toks)


def prim_svg(p, comp=None, style=''):
    rot = comp.get('rot', 0) if comp else 0
    mir = comp.get('mirror', False) if comp else False
    P = (lambda x, y: GEO.place(comp, x, y)) if comp else (lambda x, y: (x, y))
    k = p['k']
    c = style_cls(p['c'], style)
    if k in ('pl', 'pg'):
        pts = ' '.join(f'{num(x)},{num(y)}' for x, y in (P(*q) for q in p['pts']))
        return f'<{"polyline" if k == "pl" else "polygon"} class="{c}" points="{pts}"/>'
    if k == 'ci':
        x, y = P(p['x'], p['y'])
        return f'<circle class="{c}" cx="{num(x)}" cy="{num(y)}" r="{num(p["r"])}"/>'
    if k == 'rc':
        (ax, ay), (bx, by) = P(p['x'], p['y']), P(p['x'] + p['w'], p['y'] + p['h'])
        return (f'<rect class="{c}" x="{num(min(ax, bx))}" y="{num(min(ay, by))}" width="{num(abs(bx - ax))}" '
                f'height="{num(abs(by - ay))}" rx="{num(p.get("rx", 0))}"/>')
    if k == 'tx':
        x, y = P(p['x'], p['y'])
        z = p.get('z', 1)
        if p.get('ctr'):
            y += GEO.ctr_offset(p['c']) * z
        a = GEO.text_anchor(p.get('a', 'middle'), rot, mir)
        fs = f' style="font-size:{num(SYM.FONT_SIZES.get(p["c"], 12) * z)}px"' if z != 1 else ''
        inner = MU.svg_inner(p['s'], SYM.FONT_SIZES.get(p['c'], 12) * z, esc)
        return f'<text class="{p["c"]}" x="{num(x)}" y="{num(y)}" text-anchor="{a}"{fs}>{inner}</text>'
    return ''


def text_svg(x, y, s, cls='lbl', anchor='middle'):
    inner = MU.svg_inner(s, SYM.FONT_SIZES.get(cls, 12), esc)
    return f'<text class="{cls}" x="{num(x)}" y="{num(y)}" text-anchor="{anchor}">{inner}</text>'


def wire_marks(e):
    """direction marks on a wire: [distance along it to the head's base, length, half-width]; a negative length
    points back towards the wire's start"""
    out, P = [], e.get('points', [])
    cls = 'accf' if 'acc' in (e.get('style') or '').split() else 'arrow'
    for m in e.get('marks') or []:
        rem, L, W = (float(v) for v in m[:3])
        for i, (a, b) in enumerate(zip(P, P[1:])):
            n = math.hypot(b[0] - a[0], b[1] - a[1])
            if rem <= n or i == len(P) - 2:
                u = ((b[0] - a[0]) / (n or 1), (b[1] - a[1]) / (n or 1))
                base = (a[0] + u[0] * rem, a[1] + u[1] * rem)
                out.append(arrow_head(base, (base[0] + u[0] * L, base[1] + u[1] * L), cls, abs(L), W))
                break
            rem -= n
    return ''.join(out)


def arrow_size(e):
    """an arrow element's head: [length, half-width], default 9 x 4"""
    h = e.get('head') or (9, 4)
    return float(h[0]), float(h[1])


def arrow_head(a, b, cls='arrow', L=9, W=4):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1
    ux, uy = dx / n, dy / n
    bx, by = b[0] - ux * L, b[1] - uy * L
    pts = [(b[0], b[1]), (bx - uy * W, by + ux * W), (bx + uy * W, by - ux * W)]
    return f'<polygon class="{cls}" points="{" ".join(f"{num(x)},{num(y)}" for x, y in pts)}"/>'


def element_svg(e, hop=None):
    t = e['type']
    if t == 'comp':
        g = GEO.geometry(e)
        st = e.get('style', '')
        out = [prim_svg(p, e, st) for p in g['prims']]
        out += [text_svg(x, y, s, c, a) for x, y, s, c, a in GEO.label_block(e)]
        return ''.join(out)
    if t == 'wire':
        if len(e.get('points', [])) < 2:
            return ''
        cls = style_cls('w wire', e.get('style', ''))
        if hop:
            return f'<path class="{cls}" d="{GEO.wire_path(e["points"], hop)}"/>' + wire_marks(e)
        return f'<polyline class="{cls}" points="{" ".join(f"{num(x)},{num(y)}" for x, y in e["points"])}"/>' + wire_marks(e)
    if t == 'arrow':
        P = e.get('points', [])
        if len(P) < 2:
            return ''
        st = e.get('style', '')
        cls = style_cls('w', st)
        head_cls = 'accf' if 'acc' in st.split() else 'arrow'
        L, W = arrow_size(e)
        a, b = P[-2], P[-1]
        n = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
        cut = L * 2 / 3                                  # the line stops inside the head, not at its tip
        tip = (b[0] - (b[0] - a[0]) / n * cut, b[1] - (b[1] - a[1]) / n * cut)
        pts = P[:-1] + [tip]
        return (f'<polyline class="{cls}" points="{" ".join(f"{num(x)},{num(y)}" for x, y in pts)}"/>'
                + arrow_head(a, b, head_cls, L, W))
    if t == 'text':
        cls = e.get('cls', 'lbl'); lh = 16 if cls in ('note', 'title') else 14
        lines = str(e.get('text', '')).split('\n')
        return ''.join(text_svg(e['x'], e['y'] + lh * i, l, cls, e.get('anchor', 'start')) for i, l in enumerate(lines) if l != '')
    if t == 'rect':
        s = (f'<rect class="{e.get("cls", "grp")}" x="{num(e["x"])}" y="{num(e["y"])}" width="{num(e["w"])}" '
             f'height="{num(e["h"])}" rx="{num(e.get("rx", 4))}"' + (f' style="{esc(e["css"])}"' if e.get('css') else '') + '/>')
        if e.get('label'):
            s += text_svg(e['x'] + 4, e['y'] + 12, e['label'], e.get('label_cls', 'grplbl'), 'start')
        return s
    if t == 'raw':
        x, y = e.get('x', 0), e.get('y', 0)
        if x or y:
            return f'<g transform="translate({num(x)} {num(y)})">{e.get("svg", "")}</g>'
        return e.get('svg', '')
    return ''


def page_box(doc):
    pg = doc.get('page', {})
    if pg.get('auto') or not pg.get('width'):
        m = pg.get('margin', 20)
        x0, y0, x1, y1 = GEO.doc_bbox(doc)
        return (math.floor(x0 - m), math.floor(y0 - m), math.ceil(x1 - x0 + 2 * m), math.ceil(y1 - y0 + 2 * m))
    return (pg.get('x', 0), pg.get('y', 0), pg['width'], pg['height'])


def render_svg(doc, embed_fonts=False, font_urls=False, background=True) -> str:
    x, y, w, h = page_box(doc)
    meta = doc.get('meta', {})
    label = meta.get('description') or meta.get('title') or 'schematic'
    style = TH.css(doc.get('theme'))
    if embed_fonts:
        style = TH.font_faces(True) + style
    elif font_urls:
        style = TH.font_faces(False) + style
    hp = GEO.hops(doc) if doc.get('page', {}).get('hops') else {}
    body = [element_svg(e, hp.get(e.get('id'))) for e in doc['elements']]
    if doc.get('page', {}).get('junctions', True):
        manual = {GEO._key((e['x'], e['y'])) for e in doc['elements'] if e['type'] == 'comp' and e['sym'] == 'dot'}
        body += [f'<circle class="dot jn" cx="{num(px)}" cy="{num(py)}" r="3"/>'
                 for px, py in GEO.junctions(doc) if GEO._key((px, py)) not in manual]
    # background: True = the theme's paper, False / None / 'none' = transparent, or any CSS colour
    fill = TH.resolve(doc.get('theme'))['paper'] if background is True else background
    bg = (f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" fill="{esc(fill)}"/>'
          if fill and fill not in ('none', 'transparent') else '')
    vb = f'{num(x)} {num(y)} {num(w)} {num(h)}'
    return (f'<svg viewBox="{vb}" width="{num(w)}" height="{num(h)}" role="img" aria-label="{esc(label)}" '
            f'xmlns="http://www.w3.org/2000/svg"><style>{style}</style>{bg}' + ''.join(body) + '</svg>')


def to_png(svg: str, scale=2.0, theme=None) -> bytes:
    import cairosvg  # optional dependency
    from .export import cairo_svg
    return cairosvg.svg2png(bytestring=cairo_svg(svg, theme).encode(), scale=scale)


def to_pdf(svg: str, theme=None) -> bytes:
    import cairosvg
    from .export import cairo_svg
    return cairosvg.svg2pdf(bytestring=cairo_svg(svg, theme).encode())


def symbol_preview(name, props=None, size=48) -> str:
    """a small standalone SVG of one symbol (palette thumbnails, docs)"""
    doc = {'elements': [{'id': 'p', 'type': 'comp', 'sym': name, 'x': 0, 'y': 0, 'props': props or {}, 'hide_labels': True}],
           'page': {'auto': True, 'margin': 4, 'junctions': False}}
    return render_svg(doc)
