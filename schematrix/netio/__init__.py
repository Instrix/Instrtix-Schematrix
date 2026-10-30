"""Netlist files: export a document's connectivity, or import a netlist as a new schematic.

    from schematrix import netio
    text = netio.export(doc, 'kicad')                 # 'spice' | 'kicad' | 'json'
    sch = netio.import_netlist(text, filename='board.net')   # format from the name or the content

Each format is a module with export(Netlist) -> str and parse(str) -> Netlist; model.from_doc builds the
Netlist of a document and layout.to_schematic draws one.
"""
from __future__ import annotations

from . import jsonfmt, kicad, spice
from .layout import to_schematic
from .model import Netlist, Part, from_doc

FORMATS = {
    'spice': {'module': spice, 'title': 'SPICE', 'ext': ['.cir', '.sp', '.spi', '.spice', '.ckt', '.net'], 'mime': 'text/plain'},
    'kicad': {'module': kicad, 'title': 'KiCad netlist', 'ext': ['.net'], 'mime': 'text/plain'},
    'json': {'module': jsonfmt, 'title': 'Schematrix JSON netlist', 'ext': ['.json'], 'mime': 'application/json'},
}
EXT = {'spice': '.cir', 'kicad': '.net', 'json': '.netlist.json'}


def info():
    return [{'name': k, 'title': v['title'], 'ext': v['ext'], 'default_ext': EXT[k]} for k, v in FORMATS.items()]


def detect(text: str, filename: str = '') -> str:
    head = text.lstrip()[:400]
    if head.startswith('(export'):
        return 'kicad'
    if jsonfmt.looks_like(head):
        return 'json'
    fn = (filename or '').lower()
    for name, f in FORMATS.items():
        if name != 'kicad' and any(fn.endswith(e) for e in f['ext']):
            return name
    return 'spice'


def export(doc, fmt='spice', title=None) -> str:
    if fmt not in FORMATS:
        raise ValueError(f'unknown netlist format {fmt!r}; one of {", ".join(FORMATS)}')
    return FORMATS[fmt]['module'].export(from_doc(doc), title)


def parse(text: str, fmt=None, filename='') -> Netlist:
    fmt = fmt or detect(text, filename)
    if fmt not in FORMATS:
        raise ValueError(f'unknown netlist format {fmt!r}; one of {", ".join(FORMATS)}')
    return FORMATS[fmt]['module'].parse(text)


def import_netlist(text: str, fmt=None, filename='', title=None):
    """a netlist file -> a new Schematic (parts in rows, every net named by labels)"""
    nl = parse(text, fmt, filename)
    sch = to_schematic(nl, title)
    sch.warnings = list(nl.warnings)
    return sch


__all__ = ['FORMATS', 'Netlist', 'Part', 'detect', 'export', 'from_doc', 'import_netlist', 'info', 'parse', 'to_schematic']
