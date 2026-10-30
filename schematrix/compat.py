"""Run figure scripts written against the original hand-rolled `S` drawing class and get editable documents.

The original scripts (schematics.py for TR-0002) define a class `S` with methods wire/res/cap/opamp/nmos/flag/...
and figure functions that build an `S` and return `s.svg(...)`. `CompatS` has the same methods but records
editable elements (components, wires, texts) into a `Schematic`; raw `s.add(...)` markup is kept as raw elements.

    docs = import_legacy('schematics.py')        # [(name, Schematic), ...], one per figure function
"""
from __future__ import annotations

import ast
import re
import inspect
import os

from .document import Schematic

_captured: list = []


def _style(cls):
    return ' '.join(t for t in (cls or 'w').split() if t != 'w')


class CompatS:
    def __init__(self):
        self.sch = Schematic(junctions=False)
        self.sch.doc['page']['margin'] = 0
        self.p = []                       # the original exposed its parts list; scripts sometimes poke at it

    def add(self, s):
        self.sch.raw(s)

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

    def _src(self, sym, x, y1, y2, label, val, rot):
        m = (y1 + y2) / 2
        self.sch.add(sym, (x, m), rot, ref='', length=abs(y2 - y1))
        if label:
            self.sch.text(x + 24, m - 2, label, 'lbl', 'start')
        if val:
            self.sch.text(x + 24, m + 13, val, 'valsm', 'start')

    def isrc(self, x, y1, y2, label=None, val=None):
        self._src('isrc', x, y1, y2, label, val, 90)

    def vsrc(self, x, y1, y2, label=None, val=None, plus_low=False):
        self._src('vsrc', x, y1, y2, label, val, 270 if plus_low else 90)

    def box(self, x, y, w, h, title, lines=(), cls='box'):
        self.sch.add('block', (x, y), ref='', w=w, h=h, title=title, lines='\n'.join(lines), accent=(cls == 'accbox'))

    def svg(self, w, h, label):
        self.sch.page(width=w, height=h, description=label)
        _captured.append(self.sch)
        return self.sch.to_svg()


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


def import_legacy(path=None, source=None, filename='legacy.py'):
    """run a legacy figure script; return [(figure name, Schematic)] for every zero-argument function that drew one"""
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
