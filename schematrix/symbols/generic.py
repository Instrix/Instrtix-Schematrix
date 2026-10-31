"""Generic and abstract parts: blocks with named pins, impedances, Thévenin / Norton equivalents, two-ports."""
from __future__ import annotations

from .core import ENUM, FLAG, LEN, G, Prop, above, arrow, below, ci, half, leads, pg, pl, rc, symbol, two_pins, tx


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


@symbol('block', 'Block', 'Generic', 'U', 'X {*} {model}',
        {'w': Prop(160, 'num', True, label='Width'), 'h': Prop(70, 'num', True, label='Height'),
         'title': Prop('Block', 'str', True, label='Title'), 'lines': Prop('', 'text', True, label='Lines'),
         'pins': Prop('', 'str', True, label='Pins', help='e.g. "IN:l, OUT:r, VDD:t@0.5"'),
         'accent': FLAG(False, 'Accent fill'),
         'show_pins': FLAG(True, 'Pin names')},
        lines=(('ref', 'ref'),), model=lambda p: p.get('title') or 'BLOCK')
def block(p):
    w, h = float(p['w']), float(p['h'])
    prims = [rc(0, 0, w, h, 'accbox' if p['accent'] else 'box', 3), tx(w / 2, 18, str(p['title']), 'ref', fit=w - 10)]
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


@symbol('impedance', 'Impedance (generic Z)', 'Generic', 'Z', None,
        {'length': LEN(60), 'label': Prop('Z', 'str', True, label='Text inside'),
         'w': Prop(32, 'num', True, label='Body length', help='along the leads'),
         'h': Prop(16, 'num', True, label='Body width', help='across the leads'),
         'fill': ENUM('box', ['box', 'pad'], 'Fill', help='box = shaded, pad = white')})
def impedance(p):
    w, bh = max(4.0, float(p.get('w') or 32)), max(4.0, float(p.get('h') or 16))
    h = max(half(p), w / 2)
    return G([*leads(h, w / 2), rc(-w / 2, -bh / 2, w, bh, p.get('fill') or 'box', 1),
              tx(0, 0, str(p['label']), 'valsm', ctr=True, fit=w - 4)], two_pins(h), above(-bh / 2 - 6))


def _oneport(prims, label):
    """terminals a / b on the right of an equivalent circuit"""
    prims += [ci(40, -20, 3, 'pad'), ci(40, 20, 3, 'pad')]
    return G(prims, {'a': (40, -20), 'b': (40, 20)}, label)


@symbol('thevenin', 'Thévenin equivalent', 'Generic', 'TH', None,
        {'zth': Prop('Zth', 'str', True, label='Impedance text')}, lines=(('ref', 'ref'), ('value', 'val')),
        help='value: the open-circuit voltage')
def thevenin(p):
    prims = [pl([(-20, 20), (-20, 12)]), ci(-20, 0, 12, 'amp'), tx(-20, -4, '+', 'valsm', ctr=True), tx(-20, 5, '−', 'valsm', ctr=True),
             pl([(-20, -12), (-20, -20), (-6, -20)]), rc(-6, -26, 26, 12, 'box', 1), tx(7, -20, str(p['zth']), 'valsm', ctr=True, fit=23),
             pl([(20, -20), (37, -20)]), pl([(-20, 20), (37, 20)])]
    return _oneport(prims, below(30))


@symbol('norton', 'Norton equivalent', 'Generic', 'NO', None,
        {'zn': Prop('Zn', 'str', True, label='Impedance text')}, lines=(('ref', 'ref'), ('value', 'val')),
        help='value: the short-circuit current')
def norton(p):
    prims = [pl([(-20, -20), (37, -20)]), pl([(-20, 20), (37, 20)]),
             pl([(-20, -20), (-20, -12)]), pl([(-20, 12), (-20, 20)]), ci(-20, 0, 12, 'amp'), *arrow((-20, 7), (-20, -8), 5, 3),
             pl([(10, -20), (10, -13)]), pl([(10, 13), (10, 20)]), rc(4, -13, 12, 26, 'box', 1),
             tx(24, 0, str(p['zn']), 'valsm', 'start', ctr=True)]
    return _oneport(prims, below(30))


@symbol('twoport', 'Two-port network', 'Generic', 'N', 'X {1} {1n} {2} {2n} {model}',
        {'title': Prop('N', 'str', True, label='Text inside'), 'w': Prop(60, 'num', True, label='Width')},
        model=lambda p: p.get('title') or 'TWOPORT', lines=(('ref', 'ref'), ('value', 'val')))
def twoport(p):
    w = max(30.0, float(p['w'])); a = w / 2
    prims = [rc(-a, -25, w, 50, 'box', 2), tx(0, 0, str(p['title']), 'ref', ctr=True, fit=w - 8),
             pl([(-a - 10, -15), (-a, -15)]), pl([(-a - 10, 15), (-a, 15)]), pl([(a, -15), (a + 10, -15)]), pl([(a, 15), (a + 10, 15)])]
    return G(prims, {'1': (-a - 10, -15), '1n': (-a - 10, 15), '2': (a + 10, -15), '2n': (a + 10, 15)}, above(-31))


@symbol('ic', 'IC (DIP-style)', 'Generic', 'U', 'X {*} {model}',
        {'pins': Prop(8, 'num', True, label='Pins'), 'title': Prop('IC', 'str', True, label='Title'),
         'names': Prop('', 'str', True, label='Pin names', help='comma list in pin order, e.g. "VCC, IN, OUT, GND"')},
        model=lambda p: p.get('title') or 'IC', lines=(('ref', 'ref'), ('value', 'val')),
        help='pins numbered anticlockwise from top left, like a DIP package')
def ic(p):
    n = max(2, min(64, int(float(p['pins']))))
    n += n % 2
    side = n // 2
    H = 10 * side + 10
    names = [s.strip() for s in str(p['names'] or '').split(',')]
    prims = [rc(-30, 0, 60, H, 'box', 2), pg([(-4, 0), (4, 0), (0, 4)], 'w thin'), tx(0, H / 2, str(p['title']), 'valsm', ctr=True, fit=52)]
    pins = {}
    for i in range(n):
        left = i < side
        y = 10 + 10 * (i if left else n - 1 - i)
        x = -40 if left else 40
        prims.append(pl([(x, y), (-30 if left else 30, y)]))
        nm = names[i] if i < len(names) and names[i] else ''
        if nm:
            prims.append(tx(-26 if left else 26, y, nm, 'valsm', 'start' if left else 'end', ctr=True))
        prims.append(tx(x + (5 if left else -5), y - 3, str(i + 1), 'valsm', 'start' if left else 'end'))
        pins[str(i + 1)] = (x, y)
    return G(prims, pins, above(-6))
