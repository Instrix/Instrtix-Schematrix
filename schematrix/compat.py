"""Run figure scripts written against the original hand-rolled `S` drawing class and get editable documents.

The original scripts (e.g. examples/tr-0002/schematics.py) define a class `S` with methods wire/res/cap/opamp/nmos/flag/...
and figure functions that build an `S` and return `s.svg(...)`. `CompatS` has the same methods but records
editable elements (components, wires, texts) into a `Schematic`. Raw `s.add(...)` markup becomes real elements where
it is a known shape (rectangles, dashed rules, arrowheads on wires, buffer triangles and their bubbles, source circles
with a label or arrow inside); anything else is kept as a raw element. New scripts can also call rect / arrow /
buffer / diode directly.

    docs = import_legacy('schematics.py')        # [(name, Schematic), ...], one per figure function
"""
from __future__ import annotations

import ast
import inspect
import math
import os
import re

from .document import Schematic

_captured: list = []
# the original figures' line widths for flags, pads and terminals
LEGACY_THEME = {'base': 'instrix', 'lw_flag': '1.2', 'lw_pad': '1.4', 'lw_term': '1.8'}
_TAG = re.compile(r'\s*<(rect|line|polygon|circle)\b([^<>]*?)/?>\s*(?:</\1>\s*)?', re.S)
_ATTR = re.compile(r'([\w:-]+)\s*=\s*"([^"]*)"')
ACC_FILL = '#dbe8f3'


def _tag(s):
    """a single simple SVG tag -> (name, attributes), else None"""
    m = _TAG.fullmatch(s)
    return (m.group(1), dict(_ATTR.findall(m.group(2)))) if m else None


def _f(v):
    return float(v)


def _pts(s):
    nums = [float(v) for v in re.split(r'[\s,]+', s.strip()) if v]
    return [(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)]


def _near(a, b, tol=1.0):
    return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol


def _head(pts):
    """an isosceles triangle -> (tip, base middle, length, half-width), else None"""
    if len(pts) != 3:
        return None
    d = lambda a, b: math.hypot(a[0] - b[0], a[1] - b[1])
    for i in range(3):
        t, a, b = pts[i], pts[(i + 1) % 3], pts[(i + 2) % 3]
        if abs(d(t, a) - d(t, b)) < 0.05:
            m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            L = d(t, m)
            if L > 0:
                return t, m, L, d(a, b) / 2
    return None


def _style(cls):
    return ' '.join(t for t in (cls or 'w').split() if t != 'w')


class CompatS:
    embed_fonts = False                   # svg() embeds the fonts (import_legacy(embed_fonts=True), CLI --fonts)

    def __init__(self):
        self.sch = Schematic(junctions=False, theme=dict(LEGACY_THEME))
        self.sch.doc['page']['margin'] = 0
        self.p = []                       # the original exposed its parts list; scripts sometimes poke at it
        self._heads, self._circles = [], []     # raw arrowheads and source circles, resolved in svg()

    # ------------------------------------------------------------ raw markup -> elements
    def add(self, s):
        t = _tag(s) if isinstance(s, str) else None
        el = self._known(*t) if t else None
        if el is None:
            el = self.sch.raw(s)
        return el

    def _known(self, name, a):
        cls = a.get('class', '')
        try:
            if name == 'rect' and cls in ('grp', 'box', 'pad', 'accbox') and 'transform' not in a:
                css = a.get('style', '').strip().rstrip(';')
                if css.replace(' ', '').lower() == 'fill:' + ACC_FILL:
                    cls, css = 'accbox', ''
                return self.sch.rect(_f(a.get('x', 0)), _f(a.get('y', 0)), _f(a['width']), _f(a['height']), cls=cls,
                                     rx=_f(a.get('rx', 0)), back=False, css=css or None)
            if name == 'line' and a.get('stroke-dasharray', '').split() == ['2', '4'] and 'w' in cls.split():
                return self.sch.wire((_f(a['x1']), _f(a['y1'])), (_f(a['x2']), _f(a['y2'])),
                                     style=' '.join([_style(cls), 'rule']).strip())
            if name == 'polygon':
                pts = _pts(a.get('points', ''))
                if cls in ('arrow', 'accf') and _head(pts):
                    el = self.sch.raw(f'<polygon class="{cls}" points="{a["points"]}"/>')
                    self._heads.append((el, cls, _head(pts)))
                    return el
                if cls.split()[:1] == ['amp'] and len(pts) == 3:
                    return self._triangle(pts, cls)
            if name == 'circle':
                c, r = (_f(a['cx']), _f(a['cy'])), _f(a['r'])
                if cls == 'pad' and r == 4:
                    return self._bubble(c)
                if cls == 'amp' and r == 16:
                    el = self.sch.raw(f'<circle class="amp" cx="{a["cx"]}" cy="{a["cy"]}" r="16"/>')
                    self._circles.append((el, c))
                    return el
        except (KeyError, ValueError):
            return None
        return None

    def _triangle(self, pts, cls):
        """a buffer triangle: base perpendicular to an axis, tip on the base's middle"""
        hd = _head(pts)
        if not hd:
            return None
        tip, m, L, W = hd
        if abs(L - 2 * W) > 1.5 or not (abs(tip[0] - m[0]) < 0.01 or abs(tip[1] - m[1]) < 0.01):
            return None                   # not the buffer's square-ish triangle
        rot = 0 if tip[0] > m[0] + 0.01 else 180 if tip[0] < m[0] - 0.01 else 90 if tip[1] > m[1] else 270
        c = ((tip[0] + m[0]) / 2, (tip[1] + m[1]) / 2)
        return self.sch.add('buffer', c, rot, ref='', size=round(L, 2), style=' '.join(cls.split()[1:])).el

    def _bubble(self, c):
        """an r = 4 pad circle right after a buffer's tip: the buffer becomes inverting"""
        for e in reversed(self.sch.doc['elements']):
            if e.get('type') == 'comp' and e.get('sym') == 'buffer' and not e['props'].get('invert'):
                h = float(e['props'].get('size', 22)) / 2
                rad = math.radians(e.get('rot', 0))
                at = (e['x'] + (h + 4) * math.cos(rad), e['y'] + (h + 4) * math.sin(rad))
                if _near(at, c, 0.6):
                    e['props']['invert'] = True
                    return e
        return None

    def _resolve(self):
        """arrowheads onto the wires they end, source circles into sources (both may come before their parts)"""
        els = self.sch.doc['elements']
        for raw, cls, (tip, m, L, W) in self._heads:
            u = ((tip[0] - m[0]) / L, (tip[1] - m[1]) / L)
            for w in els:
                if w.get('type') != 'wire' or len(w['points']) < 2 or 'rule' in w.get('style', '').split():
                    continue
                for P in (w['points'], w['points'][::-1]):
                    e, q = P[-1], P[-2]
                    seg = (e[0] - q[0], e[1] - q[1]); n = math.hypot(*seg) or 1
                    along = (e[0] - m[0]) * u[0] + (e[1] - m[1]) * u[1]
                    off = abs((e[0] - m[0]) * u[1] - (e[1] - m[1]) * u[0])
                    if abs(seg[0] / n * u[1] - seg[1] / n * u[0]) < 0.02 and seg[0] * u[0] + seg[1] * u[1] > 0 \
                            and -1.5 <= along <= L + 1.5 and off < 1:
                        st = w.get('style', '').split()
                        if cls == 'accf' and 'acc' not in st:
                            st.append('acc')
                        wid = w['id']
                        w.clear()                 # the wire becomes the arrow, in its place in the drawing order
                        w.update({'id': wid, 'type': 'arrow',
                                  'points': [list(p) for p in P[:-1]] + [[round(tip[0], 2), round(tip[1], 2)]],
                                  'style': ' '.join(st), 'head': [round(L, 2), round(W, 2)]})
                        els.remove(raw)
                        break
                else:
                    continue
                break
        for raw, (cx, cy) in self._circles:
            label = next((e for e in els if e.get('type') == 'text' and e.get('anchor') == 'middle'
                          and _near((e['x'], e['y']), (cx, cy + 4), 0.6)), None)
            inner = next((e for e in els if e.get('type') == 'arrow'
                          and all(math.hypot(p[0] - cx, p[1] - cy) <= 16.5 for p in e['points'])), None)
            if not label and not inner:
                continue
            ends = [p for w in els if w.get('type') == 'wire' for p in (w['points'][0], w['points'][-1])]
            vertical = not any(_near(p, (cx - 16, cy)) or _near(p, (cx + 16, cy)) for p in ends) or \
                any(_near(p, (cx, cy - 16)) or _near(p, (cx, cy + 16)) for p in ends)
            if label:
                c = self.sch.add('vsrc', (cx, cy), 90 if vertical else 0, ref='', length=32, text=label['text'])
                els.remove(label)
            else:
                a, b = inner['points'][0], inner['points'][-1]
                rot = round(math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))) % 360
                c = self.sch.add('isrc', (cx, cy), rot, ref='', length=32)
                els.remove(inner)
            els.remove(c.el)
            els[els.index(raw)] = c.el            # the source takes the circle's place

    # ------------------------------------------------------------ methods for new scripts
    def rect(self, x, y, w, h, cls='grp', rx=3, label=None):
        """a rectangle (grp / box / pad / accbox); label: group caption at the top left"""
        return self.sch.rect(x, y, w, h, cls=cls, rx=rx, label=label, back=False)

    def arrow(self, *pts, cls='w', head=(9, 4)):
        """a line ending in an arrowhead; cls 'w acc' for the accent colour; head = (length, half-width)"""
        return self.sch.arrow(*pts, style=_style(cls), head=head)

    def buffer(self, x, y, size=22, cls='amp', invert=False, rot=0):
        """buffer triangle whose base is centred on (x, y) (pointing right at rot 0)"""
        rad = math.radians(rot)
        c = (x + size / 2 * math.cos(rad), y + size / 2 * math.sin(rad))
        return self.sch.add('buffer', c, rot, ref='', size=size, invert=invert, style=' '.join(cls.split()[1:]))

    def diode(self, x1, y1, x2, y2, cls='w', kind='diode'):
        """diode from anode (x1, y1) to cathode (x2, y2); kind: any diode symbol (zener, schottky, led, ...)"""
        return self._two(kind, x1, y1, x2, y2, cls)

    def wire(self, *pts, cls='w'):
        self.sch.wire(*pts, style=_style(cls))

    def dot(self, x, y):
        self.sch.dot((x, y))

    def text(self, x, y, s, a='middle', cls='lbl'):
        self.sch.text(x, y, s, cls, a)

    def _two(self, sym, x1, y1, x2, y2, cls, **props):
        st = _style(cls)
        if y1 == y2:
            L = x2 - x1
            return self.sch.add(sym, ((x1 + x2) / 2, y1), 0 if L >= 0 else 180, ref='', style=st, length=abs(L), **props)
        if x1 == x2:
            L = y2 - y1
            # rot 270 + mirror keeps the original's zigzag phase on vertical resistors
            return self.sch.add(sym, (x1, (y1 + y2) / 2), 270 if L >= 0 else 90, True, ref='', style=st, length=abs(L), **props)
        # a diagonal part: draw it as a wire, the original never does this
        self.sch.wire((x1, y1), (x2, y2), style=st)

    def res(self, x1, y1, x2, y2, cls='w', body=36):
        self._two('resistor', x1, y1, x2, y2, cls, body=body)

    def cap(self, x1, y1, x2, y2, cls='w'):
        self._two('capacitor', x1, y1, x2, y2, cls)

    def gnd(self, x, y):
        self.sch.add('ground', (x, y))

    def opamp(self, cx, cy, top='-'):
        self.sch.add('opamp', (cx, cy), ref='', top=top)

    def nmos(self, cx, cy, rot, mirror=False):
        # original: translate · scale(1 -1) · rotate(rot); here: rotate(rot') · mirror-x, so rot' = 180 - rot
        r = (180 - rot) % 360 if mirror else rot % 360
        self.sch.add('nmos', (cx, cy), r, bool(mirror), ref='')

    def switch(self, x1, x2, y):
        self.sch.add('switch', ((x1 + x2) / 2, y), ref='', length=abs(x2 - x1))

    def flag(self, x, y, label, side='left'):
        self.sch.flag((x, y), label, side)

    def term(self, x, y, label, a='start', dx=10):
        off = None if (dx == 12 and a == 'start') else [dx - 12, 0]
        c = self.sch.terminal((x, y), label, label_offset=off)
        if a != 'start':          # rare; keep the text exactly as drawn
            c.el['hide_labels'] = True
            self.sch.text(x + dx, y + 4, label, 'termlbl', a)

    def _src(self, sym, x, y1, y2, label, val, rot, **props):
        m = (y1 + y2) / 2
        self.sch.add(sym, (x, m), rot, ref='', length=abs(y2 - y1), **props)
        if label:
            self.sch.text(x + 24, m - 2, label, 'lbl', 'start')
        if val:
            self.sch.text(x + 24, m + 13, val, 'valsm', 'start')

    def isrc(self, x, y1, y2, label=None, val=None):
        self._src('isrc', x, y1, y2, label, val, 90)

    def vsrc(self, x, y1, y2, label=None, val=None, plus_low=False):
        self._src('vsrc', x, y1, y2, label, val, 270 if plus_low else 90, signs=False)
        m = (y1 + y2) / 2                 # the signs where the original put them (baselines m - 3 / m + 12)
        top, bot = ('−', '+') if plus_low else ('+', '−')
        self.sch.text(x, m - 3, top, 'pin', 'middle'); self.sch.text(x, m + 12, bot, 'pin', 'middle')

    def box(self, x, y, w, h, title, lines=(), cls='box'):
        self.sch.add('block', (x, y), ref='', w=w, h=h, title=title, lines='\n'.join(lines), accent=(cls == 'accbox'))

    def svg(self, w, h, label):
        self._resolve()
        self.sch.page(width=w, height=h, description=label)
        _captured.append(self.sch)
        return self.sch.to_svg(embed_fonts=self.embed_fonts)


def _figure_names(tree):
    """map function name -> figure file name from tuples like ('doc', 'fig-chain', chain) in the script"""
    names = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Tuple) and node.elts and isinstance(node.elts[-1], ast.Name):
            strs = [e.value for e in node.elts[:-1] if isinstance(e, ast.Constant) and isinstance(e.value, str)]
            if strs:
                names.setdefault(node.elts[-1].id, strs[-1])
    return names


def is_legacy(code: str) -> bool:
    """an old figure script built on the hand-rolled S class (it defines `class S` with an svg() method)"""
    return bool(re.search(r'^class\s+S\b', code, re.M) and re.search(r'def\s+svg\s*\(', code))


def import_legacy(path=None, source=None, filename='legacy.py', embed_fonts=False):
    """run a legacy figure script; return [(figure name, Schematic)] for every zero-argument function that drew one"""
    CompatS.embed_fonts = embed_fonts
    if source is None:
        with open(path, encoding='utf-8') as f:
            source = f.read()
        filename = path
    tree = ast.parse(source, filename)
    fig = _figure_names(tree)
    ns = {'__name__': 'schematrix_legacy', '__file__': os.path.abspath(filename)}
    exec(compile(tree, filename, 'exec'), ns)
    ns['S'] = CompatS
    out = []
    order = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
    for name in order:
        fn = ns.get(name)
        if not callable(fn):
            continue
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            continue
        if any(p.default is inspect.Parameter.empty and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
               for p in sig.parameters.values()):
            continue
        _captured.clear()
        fn()
        for i, sch in enumerate(_captured):
            title = fig.get(name, name) + (f'-{i + 1}' if len(_captured) > 1 else '')
            sch.title = title
            out.append((title, sch))
    return out
