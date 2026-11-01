"""Annotation: braces, numbered callouts, dimensions and highlight boxes. Drawing only (no pins, not in netlists)."""
from __future__ import annotations

from .core import ENUM, LEN, G, Prop, above, bez, ci, head, pl, rc, symbol, tx

TEXT = {'text': Prop('', 'str', label='Text', help='the annotation; text markup and $...$ maths work')}


@symbol('brace', 'Brace', 'Annotation', 'A', None,
        {'length': LEN(80), 'depth': Prop(8, 'num', True, label='Depth'), **TEXT}, lines=(('text', 'lbl'),),
        help='a curly brace spanning several parts; rotate it to face any side')
def brace(p):
    h, d = abs(float(p['length'])) / 2, max(2.0, float(p.get('depth') or 8))
    q = min(d, h / 2)                                   # the curls shrink on short braces
    left = [*bez((-h, 0), (-h, -d), (-h + q, -d), 8), *bez((-q, -d), (0, -d), (0, -2 * d), 8)[0:]]
    right = [(-x, y) for x, y in left]
    return G([pl(left, 'w thin'), pl(right, 'w thin')], {}, above(-2 * d - 6))


@symbol('callout', 'Callout number', 'Annotation', 'A', None,
        {'number': Prop('1', 'str', True, label='Number'), 'size': Prop(9, 'num', True, label='Radius'),
         'fill': ENUM('accent', ['accent', 'ink', 'outline'], 'Style')}, lines=(),
        help='a numbered marker for referring to parts of the figure from the text')
def callout(p):
    r = max(5.0, float(p.get('size') or 9))
    style = p.get('fill') or 'accent'
    disc = {'accent': 'callacc', 'ink': 'callink', 'outline': 'pad'}[style]
    cls = 'callnum' if style != 'outline' else 'lbl'
    return G([ci(0, 0, r, disc), tx(0, 0, str(p['number']), cls, ctr=True, fit=2 * r - 4)], {}, above(-r - 4))


@symbol('dimension', 'Dimension', 'Annotation', 'A', None,
        {'length': LEN(80), 'ext': Prop(8, 'num', True, label='Extension lines', help='0 for none'), **TEXT},
        lines=(('text', 'lbl'),), help='a measurement between two points: double arrow, extension lines and a label')
def dimension(p):
    h, e = abs(float(p['length'])) / 2, float(p.get('ext') or 0)
    prims = [pl([(-h + 3, 0), (h - 3, 0)], 'w thin'), head((-h, 0), (0, 0), 7, 3), head((h, 0), (0, 0), 7, 3)]
    if e:
        prims += [pl([(-h, -e), (-h, e)], 'w thin'), pl([(h, -e), (h, e)], 'w thin')]
    return G(prims, {}, above(-max(e, 4) - 4))


@symbol('highlight', 'Highlight box', 'Annotation', 'A', None,
        {'w': Prop(120, 'num', True, label='Width'), 'h': Prop(80, 'num', True, label='Height'), **TEXT},
        lines=(('text', 'accl'),), help='a dashed accent frame drawing the eye to part of the figure')
def highlight(p):
    w, h = max(4.0, float(p.get('w') or 120)), max(4.0, float(p.get('h') or 80))
    return G([rc(-w / 2, -h / 2, w, h, 'hl', 4)], {}, above(-h / 2 - 6))
