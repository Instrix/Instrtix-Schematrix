"""TikZ export: the drawing as a tikzpicture for LaTeX documents.

It translates the renderer's own SVG (so TikZ always matches what the editor and the SVG export show), mapping each
CSS class of the theme to TikZ line widths, colours and font sizes. Text uses the document's font, which suits the
'formal' style; sizes are kept, so a schematic sits in a 10-12 pt document at its natural scale.

    \\input{figure.tikz}                  % in a document with \\usepackage{tikz}
"""
from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET

from . import markup as MU
from . import render as R
from . import symbols as SYM
from . import theme as TH

PX = 0.75          # 1 CSS px = 0.75 pt
NS = '{http://www.w3.org/2000/svg}'

LATEX = {'\\': r'\textbackslash{}', '{': r'\{', '}': r'\}', '#': r'\#', '$': r'\$', '%': r'\%', '&': r'\&', '_': r'\_',
         '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
         'Ω': r'$\Omega$', 'µ': r'$\mu$', 'μ': r'$\mu$', '−': r'$-$', '°': r'$^\circ$', '≥': r'$\geq$', '≤': r'$\leq$',
         'Σ': r'$\Sigma$', '×': r'$\times$', 'θ': r'$\theta$', 'π': r'$\pi$', '±': r'$\pm$', '≈': r'$\approx$',
         '→': r'$\rightarrow$', '·': r'$\cdot$', '…': r'\ldots{}', 'α': r'$\alpha$', 'β': r'$\beta$', 'Δ': r'$\Delta$',
         'τ': r'$\tau$', 'ω': r'$\omega$', 'φ': r'$\varphi$', '√': r'$\surd$', '∞': r'$\infty$', '–': '--', '—': '---',
         'é': r"\'e", 'É': r"\'E", 'è': r'\`e', 'à': r'\`a', 'ç': r'\c{c}', 'ã': r'\~a', 'õ': r'\~o', 'á': r"\'a",
         'ó': r"\'o", 'í': r"\'{\i}", 'ú': r"\'u", 'ê': r'\^e', 'ô': r'\^o', 'â': r'\^a', 'ü': r'\"u', 'ö': r'\"o',
         'ä': r'\"a', '\u0305': ''}


def latex(s: str) -> str:
    return ''.join(LATEX.get(c, c) for c in s)


def _n(v) -> str:
    v = round(float(v), 2)
    return str(int(v)) if v == int(v) else f'{v:g}'


class Styles:
    """CSS classes of the theme -> TikZ options"""

    def __init__(self, theme):
        self.t = TH.resolve(theme)
        self.colors = {}

    def color(self, value) -> str:
        v = str(value).strip().lstrip('#')
        if not re.fullmatch(r'[0-9a-fA-F]{6}|[0-9a-fA-F]{3}', v):
            return 'black'
        if len(v) == 3:
            v = ''.join(c * 2 for c in v)
        v = v.upper()
        return self.colors.setdefault(v, f'sx{len(self.colors) + 1}')

    def lw(self, key) -> str:
        return f'line width={_n(float(self.t[key]) * PX)}pt'

    def shape(self, classes: set) -> str:
        t = self.t
        C = self.color
        if 'w' in classes:
            o = [f'draw={C(t["accent"] if "acc" in classes else t["wire"] if "wire" in classes else t["ink"])}']
            o.append(self.lw('lw_bus' if 'bus' in classes else 'lw_plate' if ('plate' in classes or 'acc' in classes)
                             else 'lw_thin' if 'thin' in classes else 'lw'))
            if 'para' in classes:
                o.append('dash pattern=on 3.75pt off 2.25pt')
            if 'rule' in classes:
                o.append('dash pattern=on 1.5pt off 3pt')
            o.append('line join=' + ('round' if t['join'] == 'round' else 'miter'))
            o.append('line cap=' + ('round' if t['join'] == 'round' else 'butt'))
            return ', '.join(o)
        fills = {'amp': (t['body'], t['accent'] if 'acc' in classes else t['ink'], 'lw_body'),
                 'pad': (t['paper'], t['ink'], 'lw_thin'), 'term': (t['paper'], t['ink'], 'lw_plate'),
                 'flag': (t['surface'], t['ink'], 'lw_thin'), 'box': (t['box'], t['ink'], 'lw_body'),
                 'accbox': (t['accent_fill'], t['ink'], 'lw_body'), 'grp': (t['surface'], None, None),
                 'frame': (None, t['rule'], 'lw_thin'), 'callacc': (t['accent'], None, None),
                 'callink': (t['ink'], None, None), 'tdata': (t['paper'], t['ink'], 'lw'),
                 'tdata2': (t['accent_fill'], t['ink'], 'lw'), 'tx': (t['rule'], t['ink'], 'lw'), 'gap': (t['paper'], None, None)}
        if 'grid' in classes:
            return f'draw={C(t["rule"])}, {self.lw("lw_thin")}, dash pattern=on 1.5pt off 2.25pt'
        if 'hl' in classes:
            return f'draw={C(t["accent"])}, {self.lw("lw_plate")}, dash pattern=on 4.5pt off 3pt'
        for k, (fill, draw, lw) in fills.items():
            if k in classes:
                o = [f'fill={C(fill)}'] if fill else []
                if draw:
                    o += [f'draw={C(draw)}', self.lw(lw)]
                return ', '.join(o)
        if 'jn' in classes:
            return f'fill={C(t["wire"])}'
        if classes & {'dot', 'arrow', 'accf'}:
            return f'fill={C(t["accent"] if classes & {"acc", "accf"} else t["ink"])}'
        return f'draw={C(t["ink"])}, {self.lw("lw")}'

    def text(self, cls: str, size=None) -> str:
        t = self.t
        fs = float(size) if size else SYM.FONT_SIZES.get(cls, 12)
        pt = fs * PX
        col = (t['accent'] if cls == 'accl' else t['muted'] if cls in ('val', 'valsm', 'grplbl', 'note')
               else t['paper'] if cls == 'callnum' else t['text'])
        font = [f'\\fontsize{{{_n(pt)}}}{{{_n(pt * 1.2)}}}\\selectfont']
        italic = cls == 'node' or (cls in ('ref', 'accl') and t['ref_style'] == 'italic')
        if italic:
            font.append('\\itshape')
        bold = cls in ('pin', 'termlbl', 'accl', 'grplbl', 'title', 'callnum') and int(t['strong']) >= 600
        if bold:
            font.append('\\bfseries')
        return f'font={"".join(font)}, text={self.color(col)}'


# ---------------------------------------------------------------- SVG geometry
def _pts(s):
    v = [float(x) for x in re.findall(r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?', s or '')]
    return list(zip(v[0::2], v[1::2]))


def _arc(p0, rx, ry, phi, large, sweep, p1, n=10):
    """SVG elliptical arc -> points (endpoint parameterisation, SVG spec F.6.5)"""
    (x1, y1), (x2, y2) = p0, p1
    if rx == 0 or ry == 0:
        return [p1]
    phi = math.radians(phi); c, s = math.cos(phi), math.sin(phi)
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    x1p, y1p = c * dx + s * dy, -s * dx + c * dy
    rx, ry = abs(rx), abs(ry)
    lam = x1p ** 2 / rx ** 2 + y1p ** 2 / ry ** 2
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    co = math.sqrt(max(0, num / (rx * rx * y1p * y1p + ry * ry * x1p * x1p))) * (-1 if large == sweep else 1)
    cxp, cyp = co * rx * y1p / ry, -co * ry * x1p / rx
    cx, cy = c * cxp - s * cyp + (x1 + x2) / 2, s * cxp + c * cyp + (y1 + y2) / 2
    ang = lambda ux, uy, vx, vy: math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
    t1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dt = ang((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and dt > 0:
        dt -= 2 * math.pi
    elif sweep and dt < 0:
        dt += 2 * math.pi
    out = []
    for i in range(1, n + 1):
        a = t1 + dt * i / n
        out.append((cx + rx * math.cos(a) * c - ry * math.sin(a) * s, cy + rx * math.cos(a) * s + ry * math.sin(a) * c))
    return out


def _path(d):
    """SVG path data -> list of (points, closed) subpaths; curves are sampled"""
    toks = re.findall(r'[MmLlHhVvAaCcQqZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?', d or '')
    subs, cur, pos, start = [], [], (0.0, 0.0), (0.0, 0.0)
    i, cmd = 0, None
    num = lambda: float(toks[i])
    while i < len(toks):
        if re.fullmatch(r'[A-Za-z]', toks[i]):
            cmd = toks[i]; i += 1
            if cmd in 'Zz':
                if cur:
                    subs.append((cur, True)); cur = []
                pos = start
                continue
        rel = cmd.islower(); C = cmd.upper()
        ox, oy = pos if rel else (0, 0)
        if C in 'ML':
            p = (float(toks[i]) + ox, float(toks[i + 1]) + oy); i += 2
            if C == 'M':
                if cur:
                    subs.append((cur, False))
                cur, start = [p], p
                cmd = 'l' if rel else 'L'
            else:
                cur.append(p)
            pos = p
        elif C == 'H':
            pos = (num() + ox, pos[1]); i += 1; cur.append(pos)
        elif C == 'V':
            pos = (pos[0], num() + oy); i += 1; cur.append(pos)
        elif C == 'A':
            rx, ry, ph, la, sw = (float(toks[i + k]) for k in range(5))
            p = (float(toks[i + 5]) + ox, float(toks[i + 6]) + oy); i += 7
            cur += _arc(pos, rx, ry, ph, int(la), int(sw), p); pos = p
        elif C in 'CQ':
            k = 3 if C == 'C' else 2
            ps = [(float(toks[i + 2 * j]) + ox, float(toks[i + 2 * j + 1]) + oy) for j in range(k)]; i += 2 * k
            ctrl = [pos] + ps
            for s in range(1, 11):
                t = s / 10
                pts = ctrl
                while len(pts) > 1:
                    pts = [((1 - t) * a[0] + t * b[0], (1 - t) * a[1] + t * b[1]) for a, b in zip(pts, pts[1:])]
                cur.append(pts[0])
            pos = ps[-1]
        else:
            i += 1
    if cur:
        subs.append((cur, False))
    return subs


# ---------------------------------------------------------------- conversion
def _coord(p, off):
    return f'({_n(p[0] + off[0])},{_n(p[1] + off[1])})'


def _emit(el, st, out, off=(0.0, 0.0)):
    tag = el.tag.replace(NS, '')
    classes = set((el.get('class') or '').split())
    if tag == 'g':
        m = re.match(r'translate\(\s*([-\d.e]+)[ ,]+([-\d.e]+)\s*\)', el.get('transform') or '')
        o = (off[0] + float(m.group(1)), off[1] + float(m.group(2))) if m else off
        for c in el:
            _emit(c, st, out, o)
        return
    if tag in ('style', 'title', 'desc', 'defs'):
        return
    opt = st.shape(classes) if classes else None
    if opt is None:                       # raw markup: take its presentation attributes
        o = []
        if el.get('fill') and el.get('fill') != 'none':
            o.append(f'fill={st.color(el.get("fill"))}')
        if el.get('stroke') and el.get('stroke') != 'none':
            o += [f'draw={st.color(el.get("stroke"))}', f'line width={_n(float(el.get("stroke-width", 1)) * PX)}pt']
        opt = ', '.join(o) or f'draw={st.color(st.t["ink"])}'
    if tag in ('polyline', 'polygon', 'line'):
        pts = _pts(el.get('points')) if tag != 'line' else [(float(el.get('x1', 0)), float(el.get('y1', 0))),
                                                             (float(el.get('x2', 0)), float(el.get('y2', 0)))]
        if len(pts) >= 2:
            out.append(f'\\path[{opt}] ' + ' -- '.join(_coord(p, off) for p in pts) + (' -- cycle' if tag == 'polygon' else '') + ';')
    elif tag == 'path':
        for pts, closed in _path(el.get('d')):
            if len(pts) >= 2:
                out.append(f'\\path[{opt}] ' + ' -- '.join(_coord(p, off) for p in pts) + (' -- cycle' if closed else '') + ';')
    elif tag == 'circle':
        out.append(f'\\path[{opt}] {_coord((float(el.get("cx", 0)), float(el.get("cy", 0))), off)} '
                   f'circle[radius={_n(float(el.get("r", 0)))}];')
    elif tag == 'rect':
        x, y, w, h = (float(el.get(k, 0)) for k in ('x', 'y', 'width', 'height'))
        rx = float(el.get('rx', 0) or 0)
        rc = f', rounded corners={_n(rx * PX)}pt' if rx else ''
        out.append(f'\\path[{opt}{rc}] {_coord((x, y), off)} rectangle {_coord((x + w, y + h), off)};')
    elif tag == 'text':
        cls = (el.get('class') or 'lbl').split()[0]
        m = re.search(r'font-size:\s*([\d.]+)px', el.get('style') or '')
        anchor = {'start': 'base west', 'middle': 'base', 'end': 'base east'}[el.get('text-anchor', 'start')]
        out.append(f'\\node[anchor={anchor}, inner sep=0, {st.text(cls, m.group(1) if m else None)}] at '
                   f'{_coord((float(el.get("x", 0)), float(el.get("y", 0))), off)} {{{_label(el)}}};')


def _label(el) -> str:
    """a text with $...$ maths carries its source (data-src): LaTeX gets the maths itself, not the drawing of it"""
    src = el.get('data-src')
    return MU.to_latex(src, latex) if src is not None else _runs(el)


def _runs(el) -> str:
    """a <text> with markup tspans (overline, sub / superscript by baseline shift) -> LaTeX"""
    out = [latex(el.text or '')]
    base = 0.0
    for t in el:
        base += float(t.get('dy') or 0)
        body = latex(t.text or '')
        if 'overline' in (t.get('style') or ''):
            body = f'\\ensuremath{{\\overline{{\\mbox{{{body}}}}}}}'
        if base > 0.01:
            body = f'\\textsubscript{{{body}}}'
        elif base < -0.01:
            body = f'\\textsuperscript{{{body}}}'
        out.append(body + latex(t.tail or ''))
    return ''.join(out)


def to_tikz(doc, background=True, standalone=False, scale=1.0) -> str:
    """the document as TikZ code (a tikzpicture, or a complete standalone LaTeX file)"""
    svg = R.render_svg(doc, embed_fonts=False, background=background)
    root = ET.fromstring(svg)
    st = Styles(doc.get('theme'))
    body = []
    for el in root:
        _emit(el, st, body)
    k = _n(PX * scale)
    title = doc.get('meta', {}).get('title') or 'schematic'
    head = [f'% {title}: generated by Schematrix. Needs \\usepackage{{tikz}}.',
            f'\\begin{{tikzpicture}}[x={k}pt, y=-{k}pt, line join=round]']
    head += [f'  \\definecolor{{{name}}}{{HTML}}{{{hexv}}}' for hexv, name in st.colors.items()]
    pic = '\n'.join(head + ['  ' + b for b in body] + ['\\end{tikzpicture}']) + '\n'
    if not standalone:
        return pic
    return ('\\documentclass[tikz, border=0pt]{standalone}\n\\usepackage[T1]{fontenc}\n\\usepackage{lmodern}\n'
            '\\begin{document}\n' + pic + '\\end{document}\n')
