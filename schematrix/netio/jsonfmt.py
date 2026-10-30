"""The Schematrix JSON netlist: lossless, easy to generate or consume from other tools.

    {"format": "schematrix-netlist", "version": 1, "title": "...",
     "components": [{"ref": "R1", "symbol": "resistor", "value": "1k", "part": "", "props": {}, "fields": {},
                     "pins": {"1": "VIN", "2": "VOUT"}}],
     "nets": [{"name": "VIN", "nodes": [["R1", "1"], ...]}]}

On reading, "pins" on the components is authoritative; if absent, the "nets" list is used.
"""
from __future__ import annotations

import json

from .model import Netlist, Part

FORMAT = 'schematrix-netlist'


def export(nl: Netlist, title=None) -> str:
    d = {'format': FORMAT, 'version': 1, 'title': title or nl.title,
         'components': [{'ref': p.ref, 'symbol': p.sym, 'value': p.value, 'part': p.part, 'props': p.props,
                         'fields': p.fields, 'pins': p.pins} for p in nl.parts],
         'nets': [{'name': n, 'nodes': [list(x) for x in nodes]} for n, nodes in nl.nets().items()]}
    if nl.warnings:
        d['warnings'] = nl.warnings
    return json.dumps(d, indent=1, ensure_ascii=False) + '\n'


def looks_like(text: str) -> bool:
    return FORMAT in text[:400]


def parse(text: str) -> Netlist:
    d = json.loads(text)
    if d.get('format') != FORMAT:
        raise ValueError(f'not a {FORMAT} file')
    nl = Netlist(d.get('title', ''))
    from_nets: dict = {}
    for n in d.get('nets', []):
        for ref, pin in n.get('nodes', []):
            from_nets.setdefault(ref, {})[str(pin)] = n['name']
    for c in d.get('components', []):
        ref = str(c['ref'])
        nl.parts.append(Part(ref, c.get('symbol'), str(c.get('value') or ''), str(c.get('part') or ''), c.get('props') or {},
                             {k: str(v) for k, v in (c.get('fields') or {}).items()},
                             {str(k): v for k, v in (c.get('pins') or from_nets.get(ref, {})).items()}, 'json'))
    return nl
