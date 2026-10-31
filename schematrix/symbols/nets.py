"""Net symbols and annotation: grounds, supply rails, ports, net labels, junctions, no-connect marks, test points."""
from __future__ import annotations

from ..markup import width_chars
from .core import ENUM, G, Prop, above, ci, pg, pl, right, symbol, tx


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
    return G(prims, {'p': (0, 0)}, above(lab))


@symbol('terminal', 'Terminal / port', 'Nets', 'J', None, {'label': Prop('IN', label='Label'), 'net': Prop('', label='Net')},
        lines=(('label', 'termlbl'),), net_prop='net')
def terminal(p):
    return G([ci(0, 0, 5, 'term')], {'p': (0, 0)}, right(12))


@symbol('flag', 'Net label', 'Nets', '', None,
        {'label': Prop('NET', 'str', True, label='Net name'), 'side': Prop('left', 'enum', True, ['left', 'right'], 'Side'),
         'min_width': Prop(0, 'num', True, label='Minimum width', help='give several labels the same width, e.g. 60')},
        lines=(), net_prop='label')
def flag(p):
    label = str(p['label'])
    w = max(9 + 7.2 * width_chars(label), float(p.get('min_width') or 0))     # visible text, not the markup
    s = -1 if p['side'] == 'left' else 1
    pts = [(0, 0), (s * 8, -9), (s * (8 + w), -9), (s * (8 + w), 9), (s * 8, 9)]
    return G([pg([(round(a), round(b)) for a, b in pts], 'flag'), tx(s * (8 + w / 2), 0, label, 'net', ctr=True)],
             {'p': (0, 0)})


@symbol('dot', 'Junction', 'Nets', '', None, {}, lines=())
def dot(p):
    return G([ci(0, 0, 3, 'dot')], {'p': (0, 0)})


@symbol('noconnect', 'No-connect mark', 'Nets', '', None, {}, lines=(), help='marks a pin as deliberately unconnected')
def noconnect(p):
    return G([pl([(-4, -4), (4, 4)]), pl([(-4, 4), (4, -4)])], {'p': (0, 0)})


@symbol('testpoint', 'Test point', 'Nets', 'TP', None, {'kind': ENUM('loop', ['loop', 'pad'], 'Kind')},
        lines=(('ref', 'ref'), ('value', 'val')), aliases=('TestPoint', 'TestPoint_Probe', 'TestPoint_Small'))
def testpoint(p):
    if p['kind'] == 'pad':
        return G([pl([(0, 0), (0, -8)]), ci(0, -12, 4, 'pad')], {'p': (0, 0)}, right(8, -12))
    return G([pl([(0, 0), (0, -10)]), ci(0, -15, 5, 'term')], {'p': (0, 0)}, right(9, -15))


@symbol('busentry', 'Bus entry', 'Nets', '', None, {'direction': ENUM('up', ['up', 'down'], 'Direction')}, lines=(),
        help='the 45° tap from a bus wire to a signal wire; label the bus D[7:0] and the signal D3')
def busentry(p):
    dy = -10 if p['direction'] == 'up' else 10
    return G([pl([(0, 0), (10, dy)])], {'bus': (0, 0), 'bit': (10, dy)}, buses={'bus': 0})
