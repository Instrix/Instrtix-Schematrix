"""The symbol library.

Every symbol is a function of its properties that returns *local* geometry: drawing primitives, named pins and
where its label block (ref / value / part) sits. Placement (x, y, rotation, mirror) is applied by the renderer,
so the same geometry serves the Python renderer, the netlister and the web editor (which fetches it over the API).

Local conventions: two-terminal parts lie along +x with pin 1 on the left; rotation is clockwise in 90° steps;
mirror flips local x before rotating. Primitive kinds (all JSON):

    {"k": "pl", "pts": [[x, y], ...], "c": "w"}           polyline (classes from the theme CSS)
    {"k": "pg", "pts": [[x, y], ...], "c": "amp"}         polygon
    {"k": "ci", "x": 0, "y": 0, "r": 3, "c": "dot"}       circle
    {"k": "rc", "x": 0, "y": 0, "w": 10, "h": 10, "rx": 3, "c": "box"}   rectangle (axis-aligned after rotation)
    {"k": "tx", "x": 0, "y": 0, "s": "+", "c": "pin", "a": "middle", "ctr": true}   upright text
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable

FONT_SIZES = {'lbl': 12, 'ref': 12, 'val': 11.5, 'valsm': 10.5, 'node': 12, 'net': 11, 'pin': 13, 'termlbl': 12.5,
              'accl': 12, 'grplbl': 10, 'note': 12, 'title': 15}


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


COMMON = {'ref': Prop('', label='Reference'), 'value': Prop('', label='Value'), 'part': Prop('', label='Part number')}


@dataclass
class Symbol:
    name: str
    title: str
    category: str
    fn: Callable[[dict], dict]
    props: dict = field(default_factory=dict)
    prefix: str = 'U'               # reference designator prefix
    spice: str | None = None        # SPICE element letter, or None for annotation symbols
    lines: tuple = (('ref', 'ref'), ('value', 'val'), ('part', 'valsm'))
    net_prop: str | None = None     # symbols that name the net at their pin (ground, flag, terminal, rail)
    help: str = ''

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
        g.setdefault('label', {'x': 0, 'y': -14, 'nx': 0, 'ny': -1})
        g['lines'] = [list(x) for x in self.lines]
        g['bbox'] = prim_bbox(g['prims'], g['pins'])
        return g

    def catalog_entry(self):
        return {'name': self.name, 'title': self.title, 'category': self.category, 'prefix': self.prefix,
                'spice': self.spice, 'net_prop': self.net_prop, 'help': self.help,
                'props': {k: p.spec(k) for k, p in self.all_props().items()},
                'geom_keys': self.geom_keys(), 'geometry': self.geometry()}


REGISTRY: dict[str, Symbol] = {}


def symbol(name, title, category, prefix='U', spice=None, props=None, lines=None, net_prop=None, help=''):
    def deco(fn):
        kw = {}
        if lines is not None:
            kw['lines'] = lines
        REGISTRY[name] = Symbol(name, title, category, fn, props or {}, prefix, spice, net_prop=net_prop, help=help, **kw)
        return fn
    return deco


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


def G(prims, pins, label=None):
    return {'prims': prims, 'pins': {k: [r1(v[0]), r1(v[1])] for k, v in pins.items()},
            **({'label': label} if label else {})}


LEN = lambda d, lo=20: Prop(d, 'num', geom=True, label='Length', help='pin-to-pin distance')
BODY = lambda d: Prop(d, 'num', geom=True, label='Body')


def leads(h, a):
    """the two lead wires of a 2-terminal part of half-length h whose body spans -a..a"""
    return [pl([(-h, 0), (-a, 0)]), pl([(a, 0), (h, 0)])]


# ---------------------------------------------------------------- passives
@symbol('resistor', 'Resistor', 'Passive', 'R', 'R',
        {'length': LEN(60), 'body': BODY(36), 'shape': Prop('zigzag', 'enum', True, ['zigzag', 'iec'], 'Shape')})
def resistor(p):
    L = abs(float(p['length'])); h = L / 2; body = min(float(p['body']), L); a = -body / 2
    if p['shape'] == 'iec':
        return G([*leads(h, body / 2), pl([(a, -6), (-a, -6), (-a, 6), (a, 6), (a, -6)])],
                 {'1': (-h, 0), '2': (h, 0)}, {'x': 0, 'y': -12, 'nx': 0, 'ny': -1})
    pts = [(-h, 0), (a, 0)]
    for i in range(6):
        pts.append((a + body * (i + 0.5) / 6, -6 if i % 2 == 0 else 6))
    pts += [(a + body, 0), (h, 0)]
    return G([pl(pts)], {'1': (-h, 0), '2': (h, 0)}, {'x': 0, 'y': -12, 'nx': 0, 'ny': -1})


@symbol('potentiometer', 'Potentiometer', 'Passive', 'RV', 'R', {'length': LEN(60), 'body': BODY(36)})
def potentiometer(p):
    g = resistor({**p, 'shape': 'zigzag'})
    g['prims'] += [pl([(0, -24), (0, -9)]), pg([(-3.5, -14), (3.5, -14), (0, -8)], 'arrow')]
    g['pins']['W'] = [0, -24]
    g['label'] = {'x': 0, 'y': 14, 'nx': 0, 'ny': 1}
    return g


@symbol('capacitor', 'Capacitor', 'Passive', 'C', 'C',
        {'length': LEN(40), 'polarized': Prop(False, 'bool', True, label='Polarized')})
def capacitor(p):
    h = abs(float(p['length'])) / 2
    prims = [*leads(h, 4), pl([(-4, -11), (-4, 11)], 'w plate'), pl([(4, -11), (4, 11)], 'w plate')]
    if p['polarized']:
        prims.append(tx(-12, -12, '+', 'valsm', ctr=True))
    return G(prims, {'1': (-h, 0), '2': (h, 0)}, {'x': 0, 'y': -16, 'nx': 0, 'ny': -1})


@symbol('inductor', 'Inductor', 'Passive', 'L', 'L', {'length': LEN(60), 'body': BODY(40)})
def inductor(p):
    h = abs(float(p['length'])) / 2; body = min(float(p['body']), 2 * h); a = -body / 2; r = body / 8
    pts = [(-h, 0), (a, 0)]
    for k in range(4):
        cx = a + r + 2 * r * k
        for j in range(1, 11):
            t = math.pi - math.pi * j / 10
            pts.append((cx + r * math.cos(t), -r * math.sin(t)))
    pts.append((h, 0))
    return G([pl(pts)], {'1': (-h, 0), '2': (h, 0)}, {'x': 0, 'y': -12, 'nx': 0, 'ny': -1})


@symbol('fuse', 'Fuse', 'Passive', 'F', 'R', {'length': LEN(60)})
def fuse(p):
    h = abs(float(p['length'])) / 2
    return G([*leads(h, 12), pl([(-12, -5), (12, -5), (12, 5), (-12, 5), (-12, -5)]), pl([(-12, 0), (12, 0)], 'w thin')],
             {'1': (-h, 0), '2': (h, 0)}, {'x': 0, 'y': -11, 'nx': 0, 'ny': -1})


@symbol('crystal', 'Crystal', 'Passive', 'Y', None, {'length': LEN(60)})
def crystal(p):
    h = abs(float(p['length'])) / 2
    return G([*leads(h, 10), pl([(-10, -10), (-10, 10)], 'w plate'), pl([(10, -10), (10, 10)], 'w plate'),
              pl([(-5, -12), (5, -12), (5, 12), (-5, 12), (-5, -12)])],
             {'1': (-h, 0), '2': (h, 0)}, {'x': 0, 'y': -17, 'nx': 0, 'ny': -1})


# ---------------------------------------------------------------- semiconductors
@symbol('diode', 'Diode', 'Semiconductor', 'D', 'D',
        {'length': LEN(60), 'kind': Prop('standard', 'enum', True, ['standard', 'schottky', 'zener', 'led'], 'Kind')})
def diode(p):
    h = abs(float(p['length'])) / 2
    prims = [pl([(-h, 0), (-7, 0)]), pg([(-7, -7), (-7, 7), (6, 0)]), pl([(6, 0), (h, 0)])]
    k = p['kind']
    if k == 'schottky':
        prims.append(pl([(10, -4), (10, -7), (6, -7), (6, 7), (2, 7), (2, 4)], 'w plate'))
    elif k == 'zener':
        prims.append(pl([(2, -9), (6, -7), (6, 7), (10, 9)], 'w plate'))
    else:
        prims.append(pl([(6, -7), (6, 7)], 'w plate'))
    if k == 'led':
        for dx in (-4, 3):
            prims += [pl([(dx, -10), (dx + 6, -17)]), pg([(dx + 8, -19.5), (dx + 3.2, -17.5), (dx + 6.6, -14.4)], 'arrow')]
    return G(prims, {'A': (-h, 0), 'K': (h, 0)}, {'x': 0, 'y': -12 if k != 'led' else -22, 'nx': 0, 'ny': -1})


def _mos(p, pchan):
    prims = [pl([(0, -30), (0, -15), (-9, -15)]), pl([(0, 30), (0, 15), (-9, 15)]), pl([(-9, 0), (0, 0), (0, 15)]),
             pl([(-9, -21), (-9, -9)], 'w plate'), pl([(-9, -5), (-9, 5)], 'w plate'), pl([(-9, 9), (-9, 21)], 'w plate'),
             pl([(-16, -17), (-16, 17)], 'w plate'), pl([(-30, 0), (-16, 0)]),
             pg([(-2, 0), (-8, -3.5), (-8, 3.5)] if pchan else [(-9, 0), (-3, -3.5), (-3, 3.5)], 'arrow')]
    if p.get('body_diode'):
        prims += [pl([(0, -22), (10, -22), (10, 22), (0, 22)], 'w thin'),
                  pg([(5.5, 4), (14.5, 4), (10, -3)] if not pchan else [(5.5, -4), (14.5, -4), (10, 3)], 'amp'),
                  pl([(5.5, -3), (14.5, -3)] if not pchan else [(5.5, 4), (14.5, 4)], 'w')]
    return G(prims, {'D': (0, -30), 'G': (-30, 0), 'S': (0, 30)}, {'x': 16 if p.get('body_diode') else 8, 'y': 0, 'nx': 1, 'ny': 0})


MOSPROPS = {'body_diode': Prop(False, 'bool', True, label='Body diode')}


@symbol('nmos', 'N-MOSFET', 'Semiconductor', 'Q', 'M', MOSPROPS)
def nmos(p):
    return _mos(p, False)


@symbol('pmos', 'P-MOSFET', 'Semiconductor', 'Q', 'M', MOSPROPS)
def pmos(p):
    return _mos(p, True)


def _bjt(p, pnp):
    prims = [pl([(-30, 0), (-10, 0)]), pl([(-10, -14), (-10, 14)], 'w plate'),
             pl([(-10, -6), (0, -16), (0, -30)]), pl([(-10, 6), (0, 16), (0, 30)])]
    if pnp:
        prims.append(pg([(-8.5, 7.5), (-6.2, 13.6), (-2.4, 9.8)], 'arrow'))
    else:
        prims.append(pg([(-1.5, 14.5), (-8.4, 12.2), (-3.8, 7.6)], 'arrow'))
    if p.get('envelope'):
        prims.insert(0, ci(-6, 0, 21, 'w'))
    return G(prims, {'C': (0, -30), 'B': (-30, 0), 'E': (0, 30)}, {'x': 18 if p.get('envelope') else 8, 'y': 0, 'nx': 1, 'ny': 0})


BJTPROPS = {'envelope': Prop(False, 'bool', True, label='Circle')}


@symbol('npn', 'NPN transistor', 'Semiconductor', 'Q', 'Q', BJTPROPS)
def npn(p):
    return _bjt(p, False)


@symbol('pnp', 'PNP transistor', 'Semiconductor', 'Q', 'Q', BJTPROPS)
def pnp(p):
    return _bjt(p, True)


# ---------------------------------------------------------------- amplifiers and logic
@symbol('opamp', 'Op-amp', 'Analog', 'U', 'X',
        {'top': Prop('-', 'enum', True, ['-', '+'], 'Top input'), 'supply': Prop(False, 'bool', True, label='Supply pins')})
def opamp(p):
    top = p['top']
    prims = [pg([(-30, -32), (-30, 32), (32, 0)]),
             tx(-22, -15, '−' if top == '-' else '+', 'pin', ctr=True), tx(-22, 15, '+' if top == '-' else '−', 'pin', ctr=True),
             pl([(-30, -15), (-36, -15)]), pl([(-30, 15), (-36, 15)]), pl([(32, 0), (36, 0)])]
    pins = {'inm': (-36, -15 if top == '-' else 15), 'inp': (-36, 15 if top == '-' else -15), 'out': (36, 0)}
    if p['supply']:
        prims += [pl([(0, -17), (0, -30)]), pl([(0, 17), (0, 30)])]
        pins.update({'vp': (0, -30), 'vn': (0, 30)})
    return G(prims, pins, {'x': 0, 'y': -36 if not p['supply'] else -34, 'nx': 0, 'ny': -1} if not p['supply']
             else {'x': 22, 'y': -22, 'nx': 1, 'ny': 0})


@symbol('buffer', 'Buffer / driver', 'Logic', 'U', None,
        {'invert': Prop(False, 'bool', True, label='Inverting'), 'size': Prop(22, 'num', True, label='Size')})
def buffer(p):
    s = float(p['size']); h = s / 2
    prims = [pg([(-h, -h), (-h, h), (h, 0)]), pl([(-h - 10, 0), (-h, 0)])]
    if p['invert']:
        prims += [ci(h + 4, 0, 4, 'pad'), pl([(h + 8, 0), (h + 12, 0)])]
        out = (h + 12, 0)
    else:
        prims.append(pl([(h, 0), (h + 4, 0)]))
        out = (h + 4, 0)
    return G(prims, {'in': (-h - 10, 0), 'out': out}, {'x': 0, 'y': h + 4, 'nx': 0, 'ny': 1})


def _bez(p0, c, p2, n=12):
    return [((1 - t) ** 2 * p0[0] + 2 * t * (1 - t) * c[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * t * (1 - t) * c[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]


@symbol('gate', 'Logic gate', 'Logic', 'U', None,
        {'kind': Prop('and', 'enum', True, ['and', 'nand', 'or', 'nor', 'xor', 'xnor'], 'Kind'),
         'inputs': Prop(2, 'num', True, label='Inputs')})
def gate(p):
    k = p['kind']; n = max(2, min(6, int(p['inputs'])))
    H = max(15, 5 * n)
    if k in ('and', 'nand'):
        body = [(-20, -H), (5, -H)] + [(5 + H * math.cos(t), H * math.sin(t))
                                        for t in (-math.pi / 2 + math.pi * i / 16 for i in range(17))] + [(5, H), (-20, H)]
        back = lambda y: -20
        prims = [pg(body)]
        tip = 5 + H
    else:
        top = _bez((-20, -H), (5, -H), (22, 0)); bot = _bez((22, 0), (5, H), (-20, H))
        bk = _bez((-20, H), (-10, 0), (-20, -H))
        prims = [pg(top + bot[1:] + bk[1:])]
        back = lambda y: -20 + 20 * ((1 - y / H) / 2) * (1 - (1 - y / H) / 2)
        tip = 22
        if k.startswith('x'):
            prims.append(pl(_bez((-26, H), (-16, 0), (-26, -H))))
    ys = [-(H - 5) + 2 * (H - 5) * i / (n - 1) for i in range(n)]
    pins = {}
    for i, y in enumerate(ys, 1):
        prims.append(pl([(-35, y), (back(y) if not k.startswith('x') else back(y) - 6, y)]))
        pins[f'in{i}'] = (-35, y)
    if k in ('nand', 'nor', 'xnor'):
        prims += [ci(tip + 4, 0, 4, 'pad'), pl([(tip + 8, 0), (tip + 13, 0)])]
        pins['out'] = (tip + 13, 0)
    else:
        prims.append(pl([(tip, 0), (tip + 13, 0)])); pins['out'] = (tip + 13, 0)
    return G(prims, pins, {'x': 0, 'y': -H - 6, 'nx': 0, 'ny': -1})


# ---------------------------------------------------------------- sources and switches
def _circ_src(p):
    h = abs(float(p['length'])) / 2
    return [*leads(h, 16), ci(0, 0, 16, 'amp')], h


@symbol('vsrc', 'Voltage source', 'Sources', 'V', 'V',
        {'length': LEN(100), 'kind': Prop('dc', 'enum', True, ['dc', 'ac', 'pulse'], 'Kind')})
def vsrc(p):
    prims, h = _circ_src(p)
    if p['kind'] == 'ac':
        prims.append(pl([(5 * math.sin(2 * math.pi * i / 20), -9 + 18 * i / 20) for i in range(21)]))
        prims.append(tx(-11, -10, '+', 'valsm', ctr=True))
    elif p['kind'] == 'pulse':
        prims.append(pl([(8, -8), (8, -3), (-6, -3), (-6, 3), (8, 3), (8, 8)]))
        prims.append(tx(-11, -10, '+', 'valsm', ctr=True))
    else:
        prims += [tx(-7.5, 0, '+', 'pin', ctr=True), tx(7.5, 0, '−', 'pin', ctr=True)]
    return G(prims, {'p': (-h, 0), 'n': (h, 0)}, {'x': 0, 'y': -24, 'nx': 0, 'ny': -1})


@symbol('isrc', 'Current source', 'Sources', 'I', 'I', {'length': LEN(100)})
def isrc(p):
    prims, h = _circ_src(p)
    prims += [pl([(-9, 0), (8, 0)]), pg([(3, -4), (3, 4), (10, 0)], 'arrow')]
    return G(prims, {'p': (-h, 0), 'n': (h, 0)}, {'x': 0, 'y': -24, 'nx': 0, 'ny': -1})


@symbol('battery', 'Battery', 'Sources', 'BT', 'V', {'length': LEN(40)})
def battery(p):
    h = abs(float(p['length'])) / 2
    return G([*leads(h, 3), pl([(-3, -13), (-3, 13)], 'w plate'), pl([(3, -6), (3, 6)], 'w plate'),
              tx(-10, -12, '+', 'valsm', ctr=True)],
             {'p': (-h, 0), 'n': (h, 0)}, {'x': 0, 'y': -18, 'nx': 0, 'ny': -1})


@symbol('switch', 'Switch', 'Sources', 'SW', None,
        {'length': LEN(60), 'closed': Prop(False, 'bool', True, label='Closed')})
def switch(p):
    h = abs(float(p['length'])) / 2
    lever = [(-h + 18, -1), (h - 18, -3.5)] if p['closed'] else [(-h + 18, -1), (h - 16, -13)]
    return G([pl([(-h, 0), (-h + 14, 0)]), pl([(h - 14, 0), (h, 0)]), ci(-h + 16, 0, 2.5, 'pad'), ci(h - 16, 0, 2.5, 'pad'),
              pl(lever)], {'1': (-h, 0), '2': (h, 0)}, {'x': 0, 'y': -18, 'nx': 0, 'ny': -1})


# ---------------------------------------------------------------- nets and annotation
@symbol('ground', 'Ground', 'Nets', '', None,
        {'kind': Prop('earth', 'enum', True, ['earth', 'signal', 'chassis'], 'Kind'), 'net': Prop('0', label='Net')},
        lines=(), net_prop='net')
def ground(p):
    k = p['kind']
    prims = [pl([(0, 0), (0, 8)])]
    if k == 'signal':
        prims.append(pg([(-9, 8), (9, 8), (0, 17)], 'w'))
    elif k == 'chassis':
        prims.append(pl([(-10, 8), (10, 8)]))
        prims += [pl([(x, 8), (x - 5, 15)]) for x in (-8, 0, 8)]
    else:
        prims += [pl([(-w, 8 + 4 * i), (w, 8 + 4 * i)]) for i, w in enumerate((10, 6, 2))]
    return G(prims, {'g': (0, 0)})


@symbol('rail', 'Supply rail', 'Nets', '', None,
        {'net': Prop('+5 V', label='Net'), 'kind': Prop('bar', 'enum', True, ['bar', 'arrow'], 'Kind')},
        lines=(('net', 'net'),), net_prop='net')
def rail(p):
    if p['kind'] == 'arrow':
        prims = [pl([(0, 0), (0, -8)]), pg([(-6, -8), (6, -8), (0, -16)], 'arrow')]
        lab = -21
    else:
        prims = [pl([(0, 0), (0, -10)]), pl([(-10, -10), (10, -10)], 'w plate')]
        lab = -15
    return G(prims, {'p': (0, 0)}, {'x': 0, 'y': lab, 'nx': 0, 'ny': -1})


@symbol('terminal', 'Terminal / port', 'Nets', 'J', None, {'label': Prop('IN', label='Label'), 'net': Prop('', label='Net')},
        lines=(('label', 'termlbl'),), net_prop='net')
def terminal(p):
    return G([ci(0, 0, 5, 'term')], {'p': (0, 0)}, {'x': 12, 'y': 0, 'nx': 1, 'ny': 0})


@symbol('flag', 'Net label', 'Nets', '', None,
        {'label': Prop('NET', 'str', True, label='Net name'), 'side': Prop('left', 'enum', True, ['left', 'right'], 'Side')},
        lines=(), net_prop='label')
def flag(p):
    label = str(p['label']); w = 9 + 7.2 * len(label)
    s = -1 if p['side'] == 'left' else 1
    pts = [(0, 0), (s * 8, -9), (s * (8 + w), -9), (s * (8 + w), 9), (s * 8, 9)]
    return G([pg([(round(a), round(b)) for a, b in pts], 'flag'), tx(s * (8 + w / 2), 0, label, 'net', ctr=True)],
             {'p': (0, 0)})


@symbol('dot', 'Junction', 'Nets', '', None, {}, lines=())
def dot(p):
    return G([ci(0, 0, 3, 'dot')], {'p': (0, 0)})


def parse_pins(spec: str, w, h):
    """'IN:l, OUT:r@0.5, VDD:t' -> {name: (x, y)} on the block edges (origin top-left)"""
    items = [s.strip() for s in str(spec or '').split(',') if s.strip()]
    per = {}
    for it in items:
        name, _, rest = it.partition(':')
        side, _, frac = (rest or 'l').partition('@')
        per.setdefault(side.strip()[:1].lower() or 'l', []).append((name.strip(), frac.strip()))
    pins = {}
    for side, lst in per.items():
        for i, (name, frac) in enumerate(lst):
            f = float(frac) if frac else (i + 1) / (len(lst) + 1)
            pos = {'l': (0, h * f), 'r': (w, h * f), 't': (w * f, 0), 'b': (w * f, h)}.get(side, (0, h * f))
            pins[name] = (round(pos[0] / 5) * 5 if side in 'tb' and not frac else pos[0],
                          round(pos[1] / 5) * 5 if side in 'lr' and not frac else pos[1])
    return pins


@symbol('block', 'Block', 'Blocks', 'U', 'X',
        {'w': Prop(160, 'num', True, label='Width'), 'h': Prop(70, 'num', True, label='Height'),
         'title': Prop('Block', 'str', True, label='Title'), 'lines': Prop('', 'text', True, label='Lines'),
         'pins': Prop('', 'str', True, label='Pins', help='e.g. "IN:l, OUT:r, VDD:t@0.5"'),
         'accent': Prop(False, 'bool', True, label='Accent fill'),
         'show_pins': Prop(True, 'bool', True, label='Pin names')},
        lines=(('ref', 'ref'),))
def block(p):
    w, h = float(p['w']), float(p['h'])
    prims = [rc(0, 0, w, h, 'accbox' if p['accent'] else 'box', 3), tx(w / 2, 18, str(p['title']), 'ref')]
    for i, line in enumerate([x for x in str(p['lines'] or '').split('\n') if x != ''] if p['lines'] else []):
        prims.append(tx(w / 2, 36 + 14 * i, line, 'valsm'))
    pins = parse_pins(p['pins'], w, h)
    if p['show_pins']:
        for name, (x, y) in pins.items():
            if x == 0:
                prims.append(tx(6, y, name, 'valsm', 'start', ctr=True))
            elif x == w:
                prims.append(tx(w - 6, y, name, 'valsm', 'end', ctr=True))
            elif y == 0:
                prims.append(tx(x, 14, name, 'valsm'))
            else:
                prims.append(tx(x, h - 6, name, 'valsm'))
    return G(prims, pins, {'x': w / 2, 'y': -6, 'nx': 0, 'ny': -1})


def catalog():
    order = ['Passive', 'Semiconductor', 'Analog', 'Logic', 'Sources', 'Nets', 'Blocks']
    return sorted((s.catalog_entry() for s in REGISTRY.values()), key=lambda e: (order.index(e['category']), e['title']))
