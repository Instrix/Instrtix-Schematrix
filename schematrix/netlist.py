"""Connectivity: which pins share a net, with net names from labels / terminals / rails / grounds.

Netlist file formats (SPICE, KiCad, JSON) live in the netio package; to_spice is kept here for convenience."""
from __future__ import annotations

import re

from . import geometry as GEO
from . import symbols as SYM
from .markup import plain
from .units import spice_value  # noqa: F401  (re-exported)


class UF:
    def __init__(self):
        self.p = {}

    def find(self, a):
        self.p.setdefault(a, a)
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra


BUS_NAME = re.compile(r'^(.*?)\[\s*(\d+)\s*(?::|\.\.)\s*(\d+)\s*\]$')


def bus_members(name: str):
    """'D[7:0]' or 'D[0..7]' -> ('D', [0, 1, ..., 7]): member indices low first (pin bit i is the i-th);
    a plain name -> (name, None)"""
    m = BUS_NAME.match(name)
    if not m:
        return name, None
    a, b = int(m.group(2)), int(m.group(3))
    return m.group(1), list(range(min(a, b), max(a, b) + 1))


def _is_bus_wire(w) -> bool:
    return 'bus' in (w.get('style') or '').split()


def extract(doc) -> dict:
    """{'nets': {name: [(ref, pin), ...]}, 'pins': {(comp id, pin): net}, 'warnings': [...]}

    Wires drawn in the bus style form their own layer: a plain wire touching a bus does not join it. A label on a
    bus names it 'D[7:0]'; a component's bus pin of width n on that bus connects bit i to the signal net 'D<i>'
    (as pin '<pin><i>'), which joins any signal net labelled with the same name.
    """
    wires, pts = GEO.connection_points(doc)
    K = GEO._key
    comps = {e['id']: e for e in doc['elements'] if e['type'] == 'comp'}
    bus_wires = [w for w in wires if _is_bus_wire(w)]
    on_bus = {K(p) for w in bus_wires for p in w['points']}

    def touches_bus(p):
        return K(p) in on_bus or any(GEO.on_segment(p, a, b) for w in bus_wires for a, b in zip(w['points'], w['points'][1:]))

    # every connection point gets a layer: 'b' (bus) or 's' (signal)
    layered = []
    for p, src in pts:
        if src[0] == 'pin':
            e = comps[src[1]]
            g = GEO.geometry(e)
            if src[2] in g.get('buses', {}):
                layer = 'b'
            elif SYM.get(e['sym']).net_prop and touches_bus(p):
                layer = 'b'                                   # a net label sitting on a bus names the bus
            else:
                layer = 's'
        else:
            layer = 'b' if _is_bus_wire(next(w for w in wires if w['id'] == src[1])) else 's'
        layered.append((p, src, layer))
    uf = UF()
    for p, src, L in layered:
        uf.find((L, K(p)))
    for w in wires:
        L = 'b' if _is_bus_wire(w) else 's'
        P = w['points']
        for a, b in zip(P, P[1:]):
            uf.union((L, K(a)), (L, K(b)))
            for p, _, pl in layered:
                if pl == L and GEO.on_segment(p, a, b):
                    uf.union((L, K(a)), (L, K(p)))
    layer_of = {(src[1], src[2]): L for p, src, L in layered if src[0] == 'pin'}
    root_of = lambda e, pin, p: uf.find((layer_of.get((e['id'], pin), 's'), K(p)))
    names: dict = {}
    warnings = []
    for e in comps.values():
        sym = SYM.get(e['sym'])
        if not sym.net_prop:
            continue
        props = {**sym.defaults(), **e.get('props', {})}
        name = str(props.get(sym.net_prop) or (props.get('label') if e['sym'] == 'terminal' else '') or '').strip()
        if not name:
            continue
        name = plain(name)
        for pin, p in GEO.pins(e).items():
            root = root_of(e, pin, p)
            if root in names and names[root] != name:
                warnings.append(f'net named both {names[root]!r} and {name!r}')
                continue
            names[root] = name
    # identical names join nets that are not wired together (net labels); a bus joins buses of the same base name
    by_name: dict = {}
    for root, name in list(names.items()):
        key = (root[0], bus_members(name)[0] if root[0] == 'b' else name)
        if key in by_name:
            uf.union(by_name[key], root)
        else:
            by_name[key] = root
    names = {uf.find(r): n for r, n in names.items()}
    taken = {n for n in names.values()}
    pin_net = {}
    nets: dict = {}
    auto = autob = 0
    autonames: dict = {}
    net_root: dict = {}

    def auto_name(root):
        nonlocal auto, autob
        if root not in autonames:
            if root[0] == 'b':
                autob += 1
                autonames[root] = f'BUS{autob}'
            else:
                auto += 1
                while f'N{auto:03d}' in taken:              # never reuse a name a label already gave a net
                    auto += 1
                autonames[root] = f'N{auto:03d}'
        return autonames[root]
    nc = {root_of(e, pin, p) for e in comps.values() if e['sym'] == 'noconnect' for pin, p in GEO.pins(e).items()}
    for e in sorted(comps.values(), key=lambda e: str(e.get('props', {}).get('ref') or e['id'])):
        sym = SYM.get(e['sym'])
        if not sym.is_part:
            continue
        ref = e.get('props', {}).get('ref') or e['id']
        buses = GEO.geometry(e).get('buses', {})
        for pin, p in GEO.pins(e).items():
            root = root_of(e, pin, p)
            net = names.get(root) or auto_name(root)
            if pin in buses and buses[pin] > 1:              # one connection per bit
                base, bits = bus_members(net)
                width = buses[pin]
                if bits is None:
                    bits = list(range(width))
                    base = f'{base}_' if root not in names else base
                elif len(bits) != width:
                    warnings.append(f'{ref}.{pin} is {width} bits wide but its bus {net} has {len(bits)}')
                for i in range(width):
                    member = f'{base}{bits[i]}' if i < len(bits) else f'{base}{i}?'
                    pin_net[(e['id'], f'{pin}{i}')] = member
                    nets.setdefault(member, []).append((ref, f'{pin}{i}'))
                    net_root.setdefault(member, root)
                continue
            pin_net[(e['id'], pin)] = net
            net_root[net] = root
            nets.setdefault(net, []).append((ref, pin))
    unconnected = [f'{m[0][0]}.{m[0][1]}' for n, m in nets.items()
                   if len(m) == 1 and (n.startswith('N') or n.startswith('BUS')) and net_root[n] not in nc]
    if unconnected:
        warnings.append('unconnected pins: ' + ', '.join(unconnected[:20]) + (' …' if len(unconnected) > 20 else ''))
    return {'nets': nets, 'pins': pin_net, 'warnings': warnings}


def to_spice(doc, title=None) -> str:
    from .netio import model, spice
    return spice.export(model.from_doc(doc), title)
