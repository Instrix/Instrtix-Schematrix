"""A format-neutral netlist: parts with their pin -> net map. Every reader produces one, every writer consumes one."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .. import geometry as GEO
from .. import netlist as NET
from .. import symbols as SYM

STD = ('ref', 'value', 'part')


@dataclass
class Part:
    ref: str
    sym: str | None = None                       # Schematrix symbol name (None: not resolved yet)
    value: str = ''
    part: str = ''                               # part number / SPICE model
    props: dict = field(default_factory=dict)    # other symbol properties that differ from the defaults
    fields: dict = field(default_factory=dict)   # user fields: name -> value
    pins: dict = field(default_factory=dict)     # pin name -> net name
    lib: str = ''                                # where an imported part came from (KiCad lib:part, SPICE model)

    @property
    def symbol(self):
        return SYM.REGISTRY.get(self.sym) if self.sym else None

    def all_props(self) -> dict:
        """the symbol's defaults overlaid with this part's values"""
        s = self.symbol
        d = s.defaults() if s else {}
        d.update(self.props)
        d.update({'ref': self.ref, 'value': self.value, 'part': self.part})
        return d


@dataclass
class Netlist:
    title: str = ''
    parts: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def nets(self) -> dict:
        """net name -> [(ref, pin)], in part order"""
        out: dict = {}
        for p in self.parts:
            for pin, net in p.pins.items():
                out.setdefault(net, []).append((p.ref, pin))
        return out

    def part(self, ref) -> Part:
        for p in self.parts:
            if p.ref == ref:
                return p
        raise KeyError(ref)


def fields_of(el) -> dict:
    return {f['name']: str(f.get('value', '')) for f in el.get('fields') or [] if f.get('name')}


def from_doc(doc) -> Netlist:
    """the netlist of a Schematrix document"""
    nx = NET.extract(doc)
    parts = []
    for e in doc['elements']:
        if e['type'] != 'comp':
            continue
        sym = SYM.get(e['sym'])
        if not sym.is_part:
            continue
        defaults = sym.defaults()
        props = e.get('props', {})
        allp = {**defaults, **props}
        pins = {pin: nx['pins'].get((e['id'], pin), '?') for pin in GEO.pins(e)}
        parts.append(Part(ref=str(allp.get('ref') or e['id']), sym=e['sym'], value=str(allp.get('value') or ''),
                          part=str(allp.get('part') or ''),
                          props={k: v for k, v in props.items() if k not in STD and v != defaults.get(k)},
                          fields=fields_of(e), pins=pins))
    parts.sort(key=lambda p: _natural(p.ref))
    return Netlist(doc.get('meta', {}).get('title', ''), parts, list(nx['warnings']))


def _natural(s):
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', str(s))]


GROUND_NAMES = {'0', 'GND', 'GND0', 'AGND', 'DGND', 'PGND', 'VSS', 'GNDA', 'GNDD', 'EARTH', 'CHASSIS'}


def is_ground(net: str) -> bool:
    return str(net).upper() in GROUND_NAMES
