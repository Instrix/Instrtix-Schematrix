"""Symbol machinery: properties, the registry, drawing primitives and shared drawing helpers.

Every symbol is a function of its properties that returns *local* geometry: drawing primitives, named pins and
where its label block (ref / value / part) sits. Placement (x, y, rotation, mirror) is applied by the renderer,
so the same geometry serves the Python renderer, the netlister and the web editor (which fetches it over the API).

Local conventions: two-terminal parts lie along +x with pin 1 on the left; rotation is clockwise in 90° steps;
mirror flips local x before rotating. Keep pins on the 5-unit grid. Primitive kinds (all JSON):

    {"k": "pl", "pts": [[x, y], ...], "c": "w"}           polyline (classes from the theme CSS)
    {"k": "pg", "pts": [[x, y], ...], "c": "amp"}         polygon
    {"k": "ci", "x": 0, "y": 0, "r": 3, "c": "dot"}       circle
    {"k": "rc", "x": 0, "y": 0, "w": 10, "h": 10, "rx": 3, "c": "box"}   rectangle (axis-aligned after rotation)
    {"k": "tx", "x": 0, "y": 0, "s": "+", "c": "pin", "a": "middle", "ctr": true}   upright text

Line classes: "w" ink stroke, "w plate" heavy, "w thin" light, "w para" dashed; fills: "amp" (paper),
"box" (surface), "dot"/"arrow" (ink), "pad"/"term" (hollow).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable

FONT_SIZES = {'lbl': 12, 'ref': 12, 'val': 11.5, 'valsm': 10.5, 'node': 12, 'net': 11, 'pin': 13, 'termlbl': 12.5,
              'accl': 12, 'grplbl': 10, 'note': 12, 'title': 15}

# palette order; a category not listed here sorts after these
CATEGORIES = ['Passive', 'Semiconductor', 'Analog', 'Logic', 'Sources', 'Loads & meters', 'Electromechanical',
              'Vacuum tubes', 'Signal flow', 'Generic', 'Nets']


# ---------------------------------------------------------------- primitives
def r1(v):
    return round(v, 2)


def pl(pts, c='w'):
    return {'k': 'pl', 'pts': [[r1(x), r1(y)] for x, y in pts], 'c': c}


def pg(pts, c='amp'):
    return {'k': 'pg', 'pts': [[r1(x), r1(y)] for x, y in pts], 'c': c}


def ci(x, y, r, c='dot'):
    return {'k': 'ci', 'x': r1(x), 'y': r1(y), 'r': r, 'c': c}


def rc(x, y, w, h, c='box', rx=3):
    return {'k': 'rc', 'x': r1(x), 'y': r1(y), 'w': r1(w), 'h': r1(h), 'rx': rx, 'c': c}


def tx(x, y, s, c='lbl', a='middle', ctr=False):
    return {'k': 'tx', 'x': r1(x), 'y': r1(y), 's': s, 'c': c, 'a': a, 'ctr': ctr}


def text_width(s: str, cls: str = 'lbl') -> float:
    fs = FONT_SIZES.get(cls, 12)
    return len(s) * fs * (0.55 if cls in ('note', 'title') else 0.6)


def G(prims, pins, label=None):
    """assemble a symbol's geometry"""
    return {'prims': prims, 'pins': {k: [r1(v[0]), r1(v[1])] for k, v in pins.items()},
            **({'label': label} if label else {})}


def above(y):
    """label block centred above the body, its last line at y"""
    return {'x': 0, 'y': y, 'nx': 0, 'ny': -1}


def below(y):
    return {'x': 0, 'y': y, 'nx': 0, 'ny': 1}


def right(x, y=0):
    return {'x': x, 'y': y, 'nx': 1, 'ny': 0}


# ---------------------------------------------------------------- drawing helpers
def leads(h, a):
    """the two lead wires of a 2-terminal part of half-length h whose body spans -a..a"""
    return [pl([(-h, 0), (-a, 0)]), pl([(a, 0), (h, 0)])]


def two_pins(h, a='1', b='2'):
    return {a: (-h, 0), b: (h, 0)}


def half(p, default=60):
    return abs(float(p.get('length', default))) / 2


def arc(cx, cy, r, a0, a1, n=16):
    """points on a circular arc, angles in degrees (0 = +x, 90 = +y i.e. down on screen)"""
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
            for i in range(n + 1)]


def bez(p0, c, p2, n=12):
    """quadratic Bézier points"""
    return [((1 - t) ** 2 * p0[0] + 2 * t * (1 - t) * c[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * t * (1 - t) * c[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]


def head(tip, frm, L=6, W=3.5, c='arrow'):
    """a filled arrowhead at tip, pointing away from frm"""
    dx, dy = tip[0] - frm[0], tip[1] - frm[1]
    n = math.hypot(dx, dy) or 1
    ux, uy = dx / n, dy / n
    bx, by = tip[0] - ux * L, tip[1] - uy * L
    return pg([tip, (bx - uy * W, by + ux * W), (bx + uy * W, by - ux * W)], c)


def arrow(a, b, L=6, W=3.5):
    """a line from a to b with an arrowhead at b"""
    n = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
    stop = (b[0] - (b[0] - a[0]) / n * L * 0.8, b[1] - (b[1] - a[1]) / n * L * 0.8)
    return [pl([a, stop]), head(b, a, L, W)]


def light(x, y, inward=True, n=2, gap=7, ang=-55):
    """the pair of short arrows for light: inward (photo- parts) or outward (LEDs), near (x, y)"""
    out = []
    ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    for i in range(n):
        ox = x + i * gap
        a, b = (ox, y), (ox + ux * 11, y + uy * 11)
        out += arrow(b, a, 4.5, 2.8) if inward else arrow(a, b, 4.5, 2.8)
    return out


def variable(span=16):
    """the diagonal 'adjustable' arrow drawn across a body"""
    return arrow((-span, span * 0.7), (span, -span * 0.7))


def preset(span=16):
    """the diagonal 'preset' line with a T end"""
    a, b = (-span, span * 0.7), (span, -span * 0.7)
    n = math.hypot(b[0] - a[0], b[1] - a[1]); ux, uy = (b[0] - a[0]) / n, (b[1] - a[1]) / n
    return [pl([a, b]), pl([(b[0] - uy * 4, b[1] + ux * 4), (b[0] + uy * 4, b[1] - ux * 4)])]


def coil(x0, x1, y=0, bumps=4, up=True):
    """an inductor winding from x0 to x1 along y, bumps bulging up (or down)"""
    r = (x1 - x0) / bumps / 2
    pts = []
    for k in range(bumps):
        cx = x0 + r + 2 * r * k
        pts += arc(cx, y, r, 180, 360 if up else 0, 10)[(1 if k else 0):]
    return pts


def vcoil(x, y0, y1, bumps=4, right=True):
    """a vertical winding from y0 to y1 at x, bumps bulging right (or left)"""
    r = (y1 - y0) / bumps / 2
    pts = []
    for k in range(bumps):
        cy = y0 + r + 2 * r * k
        pts += arc(x, cy, r, -90, 90 if right else -270, 10)[(1 if k else 0):]
    return pts


def iec_box(a, hh=6):
    """the rectangular resistor body spanning -a..a"""
    return pl([(-a, -hh), (a, -hh), (a, hh), (-a, hh), (-a, -hh)])


def zigzag(a, n=6, amp=6):
    pts = [(-a, 0)]
    for i in range(n):
        pts.append((-a + 2 * a * (i + 0.5) / n, -amp if i % 2 == 0 else amp))
    return pts + [(a, 0)]


# ---------------------------------------------------------------- properties and symbols
@dataclass
class Prop:
    default: Any
    type: str = 'str'          # str | num | bool | enum | text
    geom: bool = False         # changes the geometry (the editor refetches it)
    choices: list | None = None
    label: str = ''
    help: str = ''

    def spec(self, name):
        d = {'default': self.default, 'type': self.type, 'geom': self.geom, 'label': self.label or name.replace('_', ' ')}
        if self.choices:
            d['choices'] = self.choices
        if self.help:
            d['help'] = self.help
        return d


def LEN(d):
    return Prop(d, 'num', geom=True, label='Length', help='pin-to-pin distance')


def BODY(d):
    return Prop(d, 'num', geom=True, label='Body')


def ENUM(default, choices, label, geom=True, help=''):
    return Prop(default, 'enum', geom, list(choices), label, help)


def FLAG(default, label, geom=True, help=''):
    return Prop(default, 'bool', geom, label=label, help=help)


COMMON = {'ref': Prop('', label='Reference'), 'value': Prop('', label='Value'), 'part': Prop('', label='Part number')}
STD_LINES = (('ref', 'ref'), ('value', 'val'), ('part', 'valsm'))


@dataclass
class Symbol:
    name: str
    title: str
    category: str
    fn: Callable[[dict], dict]
    props: dict = field(default_factory=dict)
    prefix: str = 'U'               # reference designator prefix
    spice: str | None = None        # SPICE line template, e.g. 'R {1} {2} {value}' (see netio.spice), or None
    model: str | Callable | None = None   # default model / subcircuit name for {model}
    lines: tuple = STD_LINES
    net_prop: str | None = None     # symbols that name the net at their pin (ground, flag, terminal, rail)
    help: str = ''
    fields: tuple = ()              # suggested user fields (name, ...) offered by the editor
    pin_numbers: dict | None = None # pin name -> number for netlists (KiCad); default: digits as-is, else 1..n
    aliases: tuple = ()             # other names this symbol answers to on netlist import (KiCad lib parts, ...)
    is_part: bool | None = None     # a real component (BOM / netlist); default: it has a reference
    presets: tuple = ()             # named variants: (key, title, props[, aliases]) — own palette tile and method

    def __post_init__(self):
        if self.is_part is None:
            self.is_part = bool(self.lines) and self.lines[0][0] == 'ref' and not self.net_prop

    def all_props(self):
        d = dict(COMMON) if self.lines and self.lines[0][0] == 'ref' else {}
        d.update(self.props)
        return d

    def defaults(self):
        return {k: p.default for k, p in self.all_props().items()}

    def geom_keys(self):
        return sorted(k for k, p in self.all_props().items() if p.geom)

    def geometry(self, props: dict | None = None) -> dict:
        p = self.defaults()
        if props:
            p.update({k: v for k, v in props.items() if v is not None})
        g = self.fn(p)
        g.setdefault('label', above(-14))
        g['lines'] = [list(x) for x in self.lines]
        g['bbox'] = prim_bbox(g['prims'], g['pins'])
        return g

    def pin_names(self, props: dict | None = None) -> list:
        return list(self.geometry(props)['pins'])

    def numbering(self, props: dict | None = None) -> dict:
        """pin name -> pin number"""
        names = self.pin_names(props)
        if self.pin_numbers:
            return {n: str(self.pin_numbers.get(n, n)) for n in names}
        if all(n.isdigit() for n in names):
            return {n: n for n in names}
        return {n: str(i) for i, n in enumerate(names, 1)}

    def model_name(self, props: dict) -> str:
        m = props.get('part') or (self.model(props) if callable(self.model) else self.model)
        return str(m or self.name.upper())

    def catalog_entry(self):
        return {'name': self.name, 'title': self.title, 'category': self.category, 'prefix': self.prefix,
                'spice': self.spice[0] if self.spice else None, 'spice_template': self.spice,
                'net_prop': self.net_prop, 'help': self.help, 'fields': list(self.fields), 'is_part': self.is_part,
                'props': {k: p.spec(k) for k, p in self.all_props().items()},
                'geom_keys': self.geom_keys(), 'geometry': self.geometry(),
                'presets': [{'name': p[0], 'title': p[1], 'props': p[2], 'geometry': self.geometry(p[2])} for p in self.presets]}


REGISTRY: dict[str, Symbol] = {}
PRESETS: dict[str, tuple] = {}      # preset key -> (symbol name, props, title, aliases)


def symbol(name, title, category, prefix='U', spice=None, props=None, lines=None, net_prop=None, help='', **extra):
    """register a symbol drawing function; extra keywords are Symbol fields (model, fields, pin_numbers, ...)"""
    def deco(fn):
        if lines is not None:
            extra['lines'] = lines
        sym = REGISTRY[name] = Symbol(name, title, category, fn, props or {}, prefix, spice, net_prop=net_prop, help=help, **extra)
        for key, t, pr, *al in sym.presets:
            if key in REGISTRY or (key in PRESETS and PRESETS[key][0] != name):
                raise ValueError(f'preset {key!r} of {name} clashes with another symbol or preset')
            PRESETS[key] = (name, dict(pr), t, tuple(al[0]) if al else ())
        return fn
    return deco


def resolve(name, props=None) -> tuple:
    """a symbol or preset name -> (symbol name, props with the preset's values under the given ones)"""
    if name in PRESETS and name not in REGISTRY:
        sym, pr = PRESETS[name][:2]
        return sym, {**pr, **(props or {})}
    return name, dict(props or {})


def by_alias(part: str):
    """a foreign library part name ('D_Zener', '74HC00', 'Q_NPN_BCE') -> (symbol name, props) or None;
    preset aliases win over symbol aliases because they carry the variant"""
    low = part.lower()
    for sym, pr, _, al in PRESETS.values():
        if any(a.lower() == low for a in al):
            return sym, dict(pr)
    for s in REGISTRY.values():
        if any(a.lower() == low for a in s.aliases):
            return s.name, {}
    return None


def preset_for(name, props: dict):
    """the most specific preset of a symbol whose props all match, as (key, title, aliases), or None"""
    best = None
    for key, (sym, pr, title, al) in PRESETS.items():
        if sym == name and all(str(props.get(k)) == str(v) for k, v in pr.items()):
            if best is None or len(pr) > best[0]:
                best = (len(pr), key, title, al)
    return best[1:] if best else None


def get(name) -> Symbol:
    try:
        return REGISTRY[name]
    except KeyError:
        raise KeyError(f'unknown symbol {name!r}; known: {", ".join(sorted(REGISTRY))}') from None


def prim_bbox(prims, pins=None):
    xs, ys = [], []
    for p in prims:
        k = p['k']
        if k in ('pl', 'pg'):
            xs += [q[0] for q in p['pts']]; ys += [q[1] for q in p['pts']]
        elif k == 'ci':
            xs += [p['x'] - p['r'], p['x'] + p['r']]; ys += [p['y'] - p['r'], p['y'] + p['r']]
        elif k == 'rc':
            xs += [p['x'], p['x'] + p['w']]; ys += [p['y'], p['y'] + p['h']]
        elif k == 'tx':
            w = text_width(p['s'], p['c']); fs = FONT_SIZES.get(p['c'], 12)
            x0 = p['x'] - (w / 2 if p['a'] == 'middle' else (w if p['a'] == 'end' else 0))
            xs += [x0, x0 + w]; ys += [p['y'] - fs, p['y'] + fs * 0.3]
    for x, y in (pins or {}).values():
        xs.append(x); ys.append(y)
    if not xs:
        return [0, 0, 0, 0]
    return [r1(min(xs)), r1(min(ys)), r1(max(xs)), r1(max(ys))]


def catalog():
    rank = lambda c: CATEGORIES.index(c) if c in CATEGORIES else len(CATEGORIES)
    return sorted((s.catalog_entry() for s in REGISTRY.values()), key=lambda e: (rank(e['category']), e['category'], e['title']))
