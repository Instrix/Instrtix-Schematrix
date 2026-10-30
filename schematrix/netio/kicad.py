"""KiCad netlists (the s-expression '.net' format, version E, as written by KiCad 6-9 and read by Pcbnew).

Writing uses KiCad library names where a symbol has one (its first alias, e.g. Device:R, Device:Q_NPN_BCE) and its
KiCad pin numbering, and stores the Schematrix symbol and properties as component properties so a file written
here reads back without loss. Reading resolves foreign parts by library part name, then by reference prefix.
"""
from __future__ import annotations

import datetime as dt
import json
import re

from .. import symbols as SYM
from .model import Netlist, Part

# ---------------------------------------------------------------- s-expressions
_TOK = re.compile(r'\s*(?:(\()|(\))|"((?:\\.|[^"\\])*)"|([^\s()"]+))', re.S)


def sexp_parse(text: str):
    stack, cur = [], []
    pos = 0
    while True:
        m = _TOK.match(text, pos)
        if not m or m.end() == pos:
            break
        pos = m.end()
        if m.group(1):
            stack.append(cur); cur = []
        elif m.group(2):
            done, cur = cur, stack.pop()
            cur.append(done)
        elif m.group(3) is not None:
            cur.append(re.sub(r'\\(.)', r'\1', m.group(3)))
        else:
            cur.append(m.group(4))
    return cur[0] if len(cur) == 1 else cur


def q(s) -> str:
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'


def find(node, key):
    """first child list headed by key"""
    for c in node[1:] if isinstance(node, list) else []:
        if isinstance(c, list) and c and c[0] == key:
            return c
    return None


def find_all(node, key):
    return [c for c in (node[1:] if isinstance(node, list) else []) if isinstance(c, list) and c and c[0] == key]


def val(node, key, default=''):
    c = find(node, key)
    return c[1] if c and len(c) > 1 and isinstance(c[1], str) else default


# ---------------------------------------------------------------- writing
def lib_part(sym, props=None) -> tuple:
    """the KiCad library part to name: a matching preset's alias (D_Zener, 74HC00), else the symbol's own"""
    pre = SYM.preset_for(sym.name, props or {}) if sym else None
    if pre and pre[2]:
        return 'Device', pre[2][0]
    if sym and sym.aliases:
        return 'Device', sym.aliases[0]
    return 'Schematrix', sym.name if sym else 'unknown'


def export(nl: Netlist, title=None) -> str:
    from .. import __version__
    out = ['(export (version "E")',
           f'  (design (source {q(title or nl.title or "schematrix")}) (date {q(dt.datetime.now().isoformat(timespec="seconds"))})'
           f' (tool {q("Schematrix " + __version__)}))', '  (components']
    numbering = {}
    for p in nl.parts:
        sym = p.symbol
        numbering[p.ref] = sym.numbering(p.all_props()) if sym else {}
        lib, part = lib_part(sym, p.all_props())
        out.append(f'    (comp (ref {q(p.ref)})')
        out.append(f'      (value {q(p.value or "~")})')
        fp = p.fields.get('Footprint', '')
        out.append(f'      (footprint {q(fp)})')
        fields = {k: v for k, v in p.fields.items() if k != 'Footprint'}
        if p.part:
            fields = {'Part': p.part, **fields}
        if fields:
            out.append('      (fields ' + ' '.join(f'(field (name {q(k)}) {q(v)})' for k, v in fields.items()) + ')')
        out.append(f'      (libsource (lib {q(lib)}) (part {q(part)}) (description {q(sym.title if sym else "")}))')
        out.append(f'      (property (name "schematrix_symbol") (value {q(p.sym or "")}))')
        if p.props:
            out.append(f'      (property (name "schematrix_props") (value {q(json.dumps(p.props, ensure_ascii=False))}))')
        out[-1] += ')'
    out.append('  )')
    out.append('  (nets')
    for code, (net, nodes) in enumerate(nl.nets().items(), 1):
        out.append(f'    (net (code {q(code)}) (name {q(net)})')
        for ref, pin in nodes:
            num = numbering.get(ref, {}).get(pin, pin)
            out.append(f'      (node (ref {q(ref)}) (pin {q(num)}) (pinfunction {q(pin)}))')
        out[-1] += ')'
    out.append('  )')
    out.append(')')
    return '\n'.join(out) + '\n'


# ---------------------------------------------------------------- reading
SKIP_FIELDS = {'Reference', 'Value', 'Datasheet', 'Description', 'Sim.Device', 'Sim.Pins', 'Sim.Type', 'Sim.Library'}


PREFIXES = [('LED', 'diode', {'kind': 'led'}), ('RV', 'potentiometer', {}), ('TH', 'thermistor', {}), ('BT', 'battery', {}),
            ('SW', 'switch', {}), ('TP', 'testpoint', {}), ('FB', 'ferrite', {}), ('JP', 'jumper', {}), ('LS', 'speaker', {}),
            ('BZ', 'buzzer', {}), ('MK', 'microphone', {}), ('AE', 'antenna', {}), ('R', 'resistor', {}), ('C', 'capacitor', {}),
            ('L', 'inductor', {}), ('D', 'diode', {}), ('Q', 'npn', {}), ('F', 'fuse', {}), ('Y', 'crystal', {}),
            ('X', 'crystal', {}), ('K', 'relay', {}), ('T', 'transformer', {}), ('J', 'connector', {}), ('P', 'connector', {}),
            ('M', 'motor', {})]


def guess(ref: str, libpart: str):
    """-> (symbol name, props) or (None, {})"""
    hit = SYM.by_alias(libpart.split(':')[-1])
    if hit:
        return hit
    letters = re.match(r'^[A-Za-z]+', ref)
    pre = letters.group(0).upper() if letters else ''
    for p, name, props in PREFIXES:
        if pre == p:
            return name, dict(props)
    return None, {}


def _pin_map(sym, props, libpart, nodes) -> dict | None:
    """KiCad pin numbers / functions -> this symbol's pin names, or None if they don't fit"""
    names = sym.pin_names(props)
    by_num = {v: k for k, v in sym.numbering(props).items()}
    suffix = libpart.split(':')[-1].rsplit('_', 1)[-1]          # Q_NPN_CBE -> CBE: pins 1, 2, 3 in that order
    if len(suffix) >= 3 and all(c in names for c in suffix) and len(set(suffix)) == len(suffix):
        by_num = {str(i + 1): c for i, c in enumerate(suffix)}
    upper = {n.upper(): n for n in names}
    out = {}
    for num, func, net in nodes:
        f = (func or '').strip()
        name = upper.get(f.upper()) if f and f != '~' else None
        name = name or by_num.get(num)
        if not name:
            return None
        out[name] = net
    return out


def _block(ref, title, nodes) -> Part:
    nums = sorted({n for n, _, _ in nodes}, key=lambda s: (len(s), s))
    k = len(nums)
    spec = ', '.join(f'{n}:{"l" if i < (k + 1) // 2 else "r"}' for i, n in enumerate(nums))
    return Part(ref, 'block', '', '', {'title': title or ref, 'pins': spec, 'w': 100, 'h': max(40, 20 * ((k + 1) // 2) + 10)},
                {}, {n: net for n, _, net in nodes}, title)


def _clean_net(name, counter):
    name = name.lstrip('/')
    if name.startswith(('Net-(', 'unconnected-(')) or not name:
        counter[0] += 1
        return f'N{counter[0]:03d}'
    return name


def parse(text: str) -> Netlist:
    root = sexp_parse(text)
    if not (isinstance(root, list) and root and root[0] == 'export'):
        raise ValueError('not a KiCad netlist (no "(export" at the top)')
    nl = Netlist(val(find(root, 'design') or [], 'source').rsplit('/', 1)[-1])
    nodes: dict = {}
    counter = [0]
    for net in find_all(find(root, 'nets') or [], 'net'):
        name = _clean_net(val(net, 'name'), counter)
        for nd in find_all(net, 'node'):
            nodes.setdefault(val(nd, 'ref'), []).append((val(nd, 'pin'), val(nd, 'pinfunction'), name))
    for comp in find_all(find(root, 'components') or [], 'comp'):
        ref = val(comp, 'ref')
        value = val(comp, 'value')
        value = '' if value == '~' else value
        ls = find(comp, 'libsource') or []
        libpart = f'{val(ls, "lib")}:{val(ls, "part")}'
        props_ = {val(pr, 'name'): val(pr, 'value') for pr in find_all(comp, 'property')}
        fields = {}
        for f in find_all(find(comp, 'fields') or [], 'field'):
            nm = val(f, 'name')
            v = next((x for x in f[1:] if isinstance(x, str)), '')
            if nm and v and v != '~' and nm not in SKIP_FIELDS:
                fields[nm] = v
        fp = val(comp, 'footprint')
        if fp:
            fields.setdefault('Footprint', fp)
        part_no = fields.pop('Part', '')
        pins_in = nodes.get(ref, [])
        symname = props_.get('schematrix_symbol')
        props = json.loads(props_['schematrix_props']) if props_.get('schematrix_props') else {}
        if symname not in SYM.REGISTRY:
            symname, props = guess(ref, libpart)
        if symname == 'connector':
            nums = [int(n) for n, _, _ in pins_in if n.isdigit()]
            props['pins'] = max(nums or [2])
        pins = _pin_map(SYM.get(symname), props, libpart, pins_in) if symname else None
        if pins is None:
            if symname:
                nl.warnings.append(f'{ref}: pins of {libpart} do not match {symname}; drawn as a block')
            nl.parts.append(_block(ref, val(ls, 'part') or value, pins_in))
            continue
        nl.parts.append(Part(ref, symname, value, part_no, props, fields, pins, libpart))
    return nl
