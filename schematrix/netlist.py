"""Connectivity: which pins share a net, with net names from labels / terminals / rails / grounds.

Netlist file formats (SPICE, KiCad, JSON) live in the netio package; to_spice is kept here for convenience."""
from __future__ import annotations

from . import geometry as GEO
from . import symbols as SYM
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


def extract(doc) -> dict:
    """{'nets': {name: [(ref, pin), ...]}, 'pins': {(comp id, pin): net}, 'warnings': [...]}"""
    wires, pts = GEO.connection_points(doc)
    uf = UF()
    K = GEO._key
    for p, src in pts:
        uf.find(K(p))
    for w in wires:
        P = w['points']
        for a, b in zip(P, P[1:]):
            uf.union(K(a), K(b))
            for p, _ in pts:
                if GEO.on_segment(p, a, b):
                    uf.union(K(a), K(p))
    comps = {e['id']: e for e in doc['elements'] if e['type'] == 'comp'}
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
        for p in GEO.pins(e).values():
            root = uf.find(K(p))
            if root in names and names[root] != name:
                warnings.append(f'net named both {names[root]!r} and {name!r}')
                continue
            names[root] = name
    # identical names join nets that are not wired together (net labels)
    by_name: dict = {}
    for root, name in list(names.items()):
        if name in by_name:
            uf.union(by_name[name], root)
        else:
            by_name[name] = root
    names = {uf.find(r): n for r, n in names.items()}
    pin_net = {}
    nets: dict = {}
    auto = 0
    autonames: dict = {}
    net_root: dict = {}
    nc = {uf.find(K(p)) for e in comps.values() if e['sym'] == 'noconnect' for p in GEO.pins(e).values()}
    for e in sorted(comps.values(), key=lambda e: str(e.get('props', {}).get('ref') or e['id'])):
        sym = SYM.get(e['sym'])
        if not sym.is_part:
            continue
        ref = e.get('props', {}).get('ref') or e['id']
        for pin, p in GEO.pins(e).items():
            root = uf.find(K(p))
            if root in names:
                net = names[root]
            else:
                if root not in autonames:
                    auto += 1
                    while f'N{auto:03d}' in by_name:          # never reuse a name a label already gave a net
                        auto += 1
                    autonames[root] = f'N{auto:03d}'
                net = autonames[root]
            pin_net[(e['id'], pin)] = net
            net_root[net] = root
            nets.setdefault(net, []).append((ref, pin))
    unconnected = [f'{m[0][0]}.{m[0][1]}' for n, m in nets.items() if len(m) == 1 and n.startswith('N') and net_root[n] not in nc]
    if unconnected:
        warnings.append('unconnected pins: ' + ', '.join(unconnected[:20]) + (' …' if len(unconnected) > 20 else ''))
    return {'nets': nets, 'pins': pin_net, 'warnings': warnings}


def to_spice(doc, title=None) -> str:
    from .netio import model, spice
    return spice.export(model.from_doc(doc), title)
