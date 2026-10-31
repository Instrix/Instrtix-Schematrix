"""The scripting API: build a schematic in Python, then save it, render it or open it in the editor.

    from schematrix import Schematic
    s = Schematic('RC low-pass')
    vin = s.flag((40, 100), 'VIN', side='left')
    r = s.resistor((100, 100), value='1 kΩ')
    c = s.capacitor(anchor='1', at=r['2'], rot=90, value='10 nF')      # pin 1 of C lands on pin 2 of R
    s.gnd(c['2'])
    s.wire(vin['p'], r['1'])
    s.flag(s.wire(r['2'], (220, 100))[-1], 'VOUT', side='right')
    s.save('rc.json'); s.save_svg('rc.svg'); print(s.spice())
"""
from __future__ import annotations

import copy
import json
import os
import re
from typing import Iterable

from . import geometry as GEO
from . import netlist as NET
from . import render as R
from . import symbols as SYM

VERSION = 1
_created: list = []
_shown: list = []


class Pin(tuple):
    """an (x, y) point that also knows which component pin it is"""

    def __new__(cls, x, y, comp=None, name=None):
        t = super().__new__(cls, (x, y))
        t.comp, t.name = comp, name
        return t

    @property
    def x(self):
        return self[0]

    @property
    def y(self):
        return self[1]

    def __add__(self, d):
        return (self[0] + d[0], self[1] + d[1])

    def offset(self, dx=0, dy=0):
        return (self[0] + dx, self[1] + dy)

    def __repr__(self):
        return f'Pin({self.comp.ref if self.comp else "?"}.{self.name} @ {self[0]:g},{self[1]:g})'


class Comp:
    def __init__(self, sch, el):
        self.sch, self.el = sch, el

    id = property(lambda s: s.el['id'])
    sym = property(lambda s: s.el['sym'])
    props = property(lambda s: s.el.setdefault('props', {}))
    ref = property(lambda s: s.props.get('ref') or s.id)

    @property
    def pins(self) -> dict:
        return {k: Pin(x, y, self, k) for k, (x, y) in GEO.pins(self.el).items()}

    def __getitem__(self, name) -> Pin:
        ps = self.pins
        if name not in ps:
            raise KeyError(f'{self.ref} ({self.sym}) has no pin {name!r}; pins: {", ".join(ps)}')
        return ps[name]

    def pin(self, name):
        return self[name]

    def set(self, **props):
        self.props.update(props)
        return self

    @property
    def fields(self) -> dict:
        """user fields as {name: value}"""
        return {f['name']: f.get('value', '') for f in self.el.get('fields', [])}

    def field(self, name, value=None, show=None):
        """read a user field, or add / change it (show=True prints its value in the label block)"""
        fs = self.el.setdefault('fields', [])
        f = next((f for f in fs if f['name'] == name), None)
        if value is None and show is None:
            return f.get('value') if f else None
        if f is None:
            f = {'name': name, 'value': '', 'show': False}
            fs.append(f)
        if value is not None:
            f['value'] = str(value)
        if show is not None:
            f['show'] = bool(show)
        return self

    def remove_field(self, name):
        self.el['fields'] = [f for f in self.el.get('fields', []) if f['name'] != name]
        return self

    def move(self, dx=0, dy=0):
        self.el['x'] += dx; self.el['y'] += dy
        return self

    def moveto(self, x, y):
        self.el['x'], self.el['y'] = x, y
        return self

    @property
    def bbox(self):
        return GEO.comp_bbox(self.el)

    def __repr__(self):
        return f'<{self.sym} {self.ref} at {self.el["x"]:g},{self.el["y"]:g} rot {self.el.get("rot", 0)}>'


class Wire(list):
    """the points of a wire just added (list of (x, y)); .el is the element"""

    def __init__(self, el):
        super().__init__(tuple(p) for p in el['points'])
        self.el = el


class Schematic:
    def __init__(self, title='', width=None, height=None, *, theme='instrix', grid=5, description='',
                 junctions=True, hops=False, margin=20):
        self.doc = {'version': VERSION, 'meta': {'title': title, 'description': description},
                    'page': {'width': width, 'height': height, 'auto': width is None, 'margin': margin, 'grid': grid,
                             'junctions': junctions, 'hops': hops},
                    'theme': theme, 'elements': []}
        self._n = 0
        _created.append(self)

    # ------------------------------------------------------------ persistence
    @classmethod
    def from_dict(cls, d) -> 'Schematic':
        s = cls.__new__(cls)
        s.doc = normalize(copy.deepcopy(d))
        s._n = max([int(m.group(1)) for e in s.doc['elements'] if (m := re.match(r'e(\d+)$', str(e.get('id', ''))))] + [0])
        _created.append(s)
        return s

    @classmethod
    def load(cls, path) -> 'Schematic':
        with open(path, encoding='utf-8') as f:
            return cls.from_dict(json.load(f))

    def to_dict(self):
        return copy.deepcopy(self.doc)

    def to_json(self, indent=1):
        from .symbols import custom as CUSTOM
        used = CUSTOM.used_in(self.doc)                 # carry user-drawn symbols so the file opens anywhere
        doc = {**self.doc, 'symbols': used} if used else {k: v for k, v in self.doc.items() if k != 'symbols'}
        return json.dumps(doc, indent=indent, ensure_ascii=False)

    def save(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
        return path

    # ------------------------------------------------------------ rendering / export
    def to_svg(self, embed_fonts=False, **kw) -> str:
        return R.render_svg(self.doc, embed_fonts=embed_fonts, **kw)

    def save_svg(self, path, embed_fonts=False):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.to_svg(embed_fonts=embed_fonts))
        return path

    def save_png(self, path, scale=2.0):
        with open(path, 'wb') as f:
            f.write(R.to_png(self.to_svg(), scale, self.doc.get('theme')))
        return path

    def export(self, path, fmt=None, **options):
        """write any export format (svg, png, jpeg, webp, pdf, eps, tikz, tex) chosen by fmt or the extension.
        options: ids=[...] (only those elements, cropped), background=True | False | '#fff', scale=, margin=, fonts="""
        from . import export as EX
        fmt = fmt or os.path.splitext(str(path))[1].lstrip('.').lower()
        data = EX.export(self.doc, fmt, **options)[0]
        with open(path, 'wb') as f:
            f.write(data)
        return path

    def to_tikz(self, standalone=False, background=False) -> str:
        from . import tikz
        return tikz.to_tikz(self.doc, background=background, standalone=standalone)

    def save_pdf(self, path):
        with open(path, 'wb') as f:
            f.write(R.to_pdf(self.to_svg(), self.doc.get('theme')))
        return path

    def _repr_svg_(self):  # Jupyter
        return self.to_svg(embed_fonts=True)

    def netlist(self) -> dict:
        return NET.extract(self.doc)

    def spice(self) -> str:
        return NET.to_spice(self.doc)

    def directive(self, *lines):
        """add SPICE lines to the netlist: analyses (.tran 1u 1m, .ac dec 20 10 1Meg), .model, .include, .param ..."""
        self.doc.setdefault('spice', []).extend(str(x) for x in lines)
        return self

    def export_netlist(self, fmt='spice') -> str:
        """netlist text: 'spice', 'kicad' or 'json'"""
        from . import netio
        return netio.export(self.doc, fmt)

    def save_netlist(self, path, fmt=None):
        """write a netlist; the format follows the extension (.cir/.sp spice, .net kicad, .json json) unless given"""
        from . import netio
        p = str(path).lower()
        fmt = fmt or ('json' if p.endswith('.json') else 'kicad' if p.endswith('.net') else 'spice')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(netio.export(self.doc, fmt))
        return path

    @classmethod
    def from_netlist(cls, source, fmt=None, title=None) -> 'Schematic':
        """a new schematic from netlist text or a netlist file path (SPICE, KiCad .net or Schematrix JSON)"""
        from . import netio
        name = ''
        if isinstance(source, os.PathLike) or (isinstance(source, str) and '\n' not in source and os.path.isfile(source)):
            name = str(source)
            with open(source, encoding='utf-8') as f:
                source = f.read()
        return netio.import_netlist(source, fmt, name, title)

    def show(self):
        """mark this schematic as the script's result (the editor opens the shown schematics)"""
        if self not in _shown:
            _shown.append(self)
        return self

    # ------------------------------------------------------------ page
    title = property(lambda s: s.doc['meta'].get('title', ''), lambda s, v: s.doc['meta'].__setitem__('title', v))

    def page(self, width=None, height=None, auto=None, margin=None, grid=None, junctions=None, hops=None, theme=None, description=None):
        pg = self.doc['page']
        for k, v in (('width', width), ('height', height), ('margin', margin), ('grid', grid), ('junctions', junctions),
                     ('hops', hops)):
            if v is not None:
                pg[k] = v
        if width is not None and auto is None:
            pg['auto'] = False
        if auto is not None:
            pg['auto'] = auto
        if theme is not None:
            self.doc['theme'] = theme
        if description is not None:
            self.doc['meta']['description'] = description
        return self

    def frame(self, size='A4', orientation='landscape', **fields):
        """a drawing border with zones and a title block; fields: title, subtitle, company, doc, rev, author, date,
        sheet. The page takes the paper size; size=None removes the frame."""
        from . import frame as FR
        FR.apply(self.doc, size, orientation, fields)
        return self

    def fit(self, margin=20):
        """size the page to the drawing"""
        x, y, w, h = R.page_box({**self.doc, 'page': {**self.doc['page'], 'auto': True, 'margin': margin}})
        self.doc['page'].update(x=x, y=y, width=w, height=h, auto=False)
        return self

    # ------------------------------------------------------------ elements
    def _id(self):
        self._n += 1
        while any(e.get('id') == f'e{self._n}' for e in self.doc['elements']):
            self._n += 1
        return f'e{self._n}'

    def _push(self, el, back=False):
        el['id'] = el.get('id') or self._id()
        if back:
            self.doc['elements'].insert(0, el)
        else:
            self.doc['elements'].append(el)
        return el

    def next_ref(self, prefix):
        used = {e.get('props', {}).get('ref') for e in self.doc['elements'] if e['type'] == 'comp'}
        i = 1
        while f'{prefix}{i}' in used:
            i += 1
        return f'{prefix}{i}'

    def add(self, sym, at=(0, 0), rot=0, mirror=False, *, anchor=None, ref=None, value=None, part=None, style='',
            label_offset=None, hide_labels=False, id=None, fields=None, **props) -> Comp:
        """place a symbol. fields: {name: value} (hidden), {name: (value, show)} or [{'name', 'value', 'show'}]"""
        sym, props = SYM.resolve(sym, props)        # presets ('zener', 'nand_gate', ...) are a symbol plus props
        s = SYM.get(sym)
        if s.lines and s.lines[0][0] == 'ref' and ref is None and s.prefix:
            ref = self.next_ref(s.prefix)
        for k, v in (('ref', ref), ('value', value), ('part', part)):
            if v is not None:
                props[k] = v
        unknown = set(props) - set(s.all_props())
        if unknown:
            raise TypeError(f'{sym} has no properties {sorted(unknown)}; it has {sorted(s.all_props())}')
        el = {'type': 'comp', 'sym': sym, 'x': float(at[0]), 'y': float(at[1]), 'rot': int(rot) % 360,
              'mirror': bool(mirror), 'props': props, 'style': style}
        if id:
            el['id'] = id
        if label_offset:
            el['label_offset'] = list(label_offset)
        if hide_labels:
            el['hide_labels'] = True
        if fields:
            el['fields'] = norm_fields(fields)
        if anchor is not None:
            local = GEO.geometry(el)['pins'][anchor]
            dx, dy = GEO.xf(*local, el['rot'], el['mirror'])
            el['x'], el['y'] = float(at[0]) - dx, float(at[1]) - dy
        for k in ('x', 'y'):
            if el[k] == int(el[k]):
                el[k] = int(el[k])
        self._push(el)
        return Comp(self, el)

    def __getattr__(self, name):
        if name.startswith('_') or (name not in SYM.REGISTRY and name not in SYM.PRESETS):
            raise AttributeError(name)

        def make(at=(0, 0), rot=0, mirror=False, **kw):
            return self.add(name, at, rot, mirror, **kw)
        make.__doc__ = f'add a {SYM.REGISTRY[name].title if name in SYM.REGISTRY else SYM.PRESETS[name][2]}'
        return make

    # shorthand for the net symbols, which take their name positionally
    def flag(self, at, label, side='left', rot=0, **kw):
        return self.add('flag', at, rot, label=label, side=side, **kw)

    def terminal(self, at, label, rot=0, **kw):
        return self.add('terminal', at, rot, label=label, **kw)

    def gnd(self, at, kind='earth', rot=0, **kw):
        return self.add('ground', at, rot, kind=kind, **kw)

    def rail(self, at, net, kind='bar', rot=0, **kw):
        return self.add('rail', at, rot, net=net, kind=kind, **kw)

    def dot(self, at):
        return self.add('dot', at)

    def wire(self, *pts, style='') -> Wire:
        pts = [p for p in pts if p is not None]
        el = self._push({'type': 'wire', 'points': [[_n(p[0]), _n(p[1])] for p in pts], 'style': style})
        return Wire(el)

    def route(self, a, b, how='auto', style='') -> Wire:
        """orthogonal wire from a to b: 'hv' (horizontal first), 'vh', 'hvh' / 'vhv' (dog-leg) or 'auto'"""
        (x1, y1), (x2, y2) = a, b
        if how == 'auto':
            how = 'hv' if abs(x2 - x1) >= abs(y2 - y1) else 'vh'
        if x1 == x2 or y1 == y2:
            pts = [a, b]
        elif how == 'hv':
            pts = [a, (x2, y1), b]
        elif how == 'vh':
            pts = [a, (x1, y2), b]
        elif how == 'hvh':
            m = (x1 + x2) / 2; pts = [a, (m, y1), (m, y2), b]
        elif how == 'vhv':
            m = (y1 + y2) / 2; pts = [a, (x1, m), (x2, m), b]
        else:
            raise ValueError(how)
        return self.wire(*pts, style=style)

    def connect(self, *pins, how='auto', style=''):
        """chain orthogonal routes through several points"""
        return [self.route(a, b, how, style) for a, b in zip(pins, pins[1:])]

    def text(self, x, y, s, cls='lbl', anchor='start'):
        return self._push({'type': 'text', 'x': x, 'y': y, 'text': str(s), 'cls': cls, 'anchor': anchor})

    def note(self, x, y, s, anchor='start'):
        return self.text(x, y, s, 'note', anchor)

    def heading(self, x, y, s, anchor='start'):
        return self.text(x, y, s, 'title', anchor)

    def rect(self, x, y, w, h, cls='grp', label=None, rx=4, back=True, css=None):
        el = {'type': 'rect', 'x': x, 'y': y, 'w': w, 'h': h, 'cls': cls, 'rx': rx}
        if label:
            el['label'] = label
        if css:
            el['css'] = css
        return self._push(el, back=back)

    def group(self, comps: Iterable, label=None, pad=12, cls='grp'):
        """a shaded group rectangle behind some components"""
        bs = [c.bbox if isinstance(c, Comp) else GEO.element_bbox(c) for c in comps]
        x0 = min(b[0] for b in bs) - pad; y0 = min(b[1] for b in bs) - pad - (12 if label else 0)
        x1 = max(b[2] for b in bs) + pad; y1 = max(b[3] for b in bs) + pad
        return self.rect(round(x0), round(y0), round(x1 - x0), round(y1 - y0), cls, label)

    def arrow(self, *pts, style='acc', head=None):
        """a line ending in an arrowhead; style 'acc' (accent colour) or '' (ink); head = (length, half-width),
        default (9, 4)"""
        el = {'type': 'arrow', 'points': [[_n(p[0]), _n(p[1])] for p in pts], 'style': style}
        if head:
            el['head'] = [_n(head[0]), _n(head[1])]
        return self._push(el)

    def raw(self, svg, x=0, y=0, bbox=None):
        el = {'type': 'raw', 'svg': svg, 'x': x, 'y': y}
        if bbox:
            el['bbox'] = bbox
        return self._push(el)

    # ------------------------------------------------------------ queries
    def comps(self, sym=None):
        return [Comp(self, e) for e in self.doc['elements'] if e['type'] == 'comp' and (sym is None or e['sym'] == sym)]

    def find(self, ref) -> Comp:
        for c in self.comps():
            if c.ref == ref or c.id == ref:
                return c
        raise KeyError(ref)

    def __getitem__(self, ref):
        return self.find(ref)

    def __repr__(self):
        n = len(self.doc['elements'])
        return f'<Schematic {self.title!r}: {n} elements>'


def norm_fields(fields) -> list:
    """{name: value} | {name: (value, show)} | [{'name', 'value', 'show'}] -> the document's field list"""
    if isinstance(fields, dict):
        out = []
        for k, v in fields.items():
            val, show = (v if isinstance(v, (tuple, list)) else (v, False))
            out.append({'name': str(k), 'value': str(val), 'show': bool(show)})
        return out
    return [{'name': str(f['name']), 'value': str(f.get('value', '')), 'show': bool(f.get('show'))} for f in fields]


def _n(v):
    v = round(float(v), 2)
    return int(v) if v == int(v) else v


def normalize(d: dict) -> dict:
    """fill defaults and check a document dict (from JSON, the API or an old version)"""
    if not isinstance(d, dict) or 'elements' not in d:
        raise ValueError('not a Schematrix document (no "elements")')
    d.setdefault('version', VERSION)
    d.setdefault('meta', {}).setdefault('title', '')
    pg = d.setdefault('page', {})
    pg.setdefault('grid', 5); pg.setdefault('margin', 20); pg.setdefault('junctions', True); pg.setdefault('hops', False)
    pg.setdefault('auto', not pg.get('width'))
    d.setdefault('theme', 'instrix')
    from .symbols import custom as CUSTOM
    for name, defn in (d.get('symbols') or {}).items():       # custom symbols travel inside the document
        if name not in SYM.REGISTRY:
            try:
                CUSTOM.register(defn)
            except ValueError:
                pass
    seen = set()
    for i, e in enumerate(d['elements']):
        if 'type' not in e:
            raise ValueError(f'element {i} has no type')
        if e['type'] == 'comp':
            SYM.get(e['sym'])
            e.setdefault('rot', 0); e.setdefault('mirror', False); e.setdefault('props', {})
        if not e.get('id') or e['id'] in seen:
            e['id'] = f'x{i + 1}'
        seen.add(e['id'])
    return d


def shown_or_created():
    return list(_shown) or list(_created)


def reset_registry():
    _created.clear(); _shown.clear()


def load(path) -> Schematic:
    return Schematic.load(path)
