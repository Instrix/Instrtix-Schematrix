"""Engineering values: '1 kΩ' <-> SPICE '1k'."""
from __future__ import annotations

import re

_SI = {'f': 'f', 'p': 'p', 'n': 'n', 'u': 'u', 'µ': 'u', 'μ': 'u', 'm': 'm', 'k': 'k', 'K': 'k', 'M': 'Meg', 'G': 'G', 'T': 'T'}
_NUM = re.compile(r'^([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)\s*([fpnuµμmkKMGT]?)\s*(Ω|ohm|F|H|V|A|Hz|s)?$')


def spice_value(v: str) -> str:
    """'1 kΩ' -> '1k', '10 mΩ' -> '10m', '4.7 µF' -> '4.7u', '2.2 MΩ' -> '2.2Meg', '30.1k' -> '30.1k'"""
    from .markup import plain
    s = plain(str(v or '')).strip()
    m = _NUM.match(s)
    if not m:
        return s.replace(' ', '') or '?'
    n, pre, _unit = m.groups()
    return n + _SI.get(pre, '') if pre else n


def is_number(v: str) -> bool:
    return bool(re.match(r'^[-+]?\d', str(v or '').strip()))
