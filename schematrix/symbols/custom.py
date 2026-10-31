"""User-drawn symbols: plain JSON definitions, registered next to the built-in library.

    {"name": "ldo_3v3", "title": "3.3 V LDO", "category": "Custom", "prefix": "U",
     "prims": [{"k": "rc", "x": -30, "y": -20, "w": 60, "h": 40, "c": "box", "rx": 2}, ...],
     "pins": {"IN": [-40, 0], "OUT": [40, 0], "GND": [0, 30]},
     "label": {"x": 0, "y": -26, "nx": 0, "ny": -1},
     "spice": "X {IN} {GND} {OUT} {model}", "fields": ["Output voltage"], "help": ""}

The editor's symbol editor writes these into the workspace's symbols/ folder; documents that use one carry a copy
under doc["symbols"], so they render anywhere. Primitives are the same JSON the built-in symbols produce (core.py).
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

from .core import CATEGORIES, REGISTRY, G, Symbol, prim_bbox

NAME = re.compile(r'^[a-z][a-z0-9_]{1,47}$')
KINDS = {'pl', 'pg', 'ci', 'rc', 'tx'}
CLASSES = {'w', 'w plate', 'w thin', 'w para', 'w thin para', 'w bus', 'amp', 'box', 'accbox', 'dot', 'arrow', 'pad',
           'term', 'flag', 'lbl', 'ref', 'val', 'valsm', 'pin', 'net', 'note'}
CUSTOM_CATEGORY = 'Custom'
if CUSTOM_CATEGORY not in CATEGORIES:
    CATEGORIES.insert(len(CATEGORIES) - 1, CUSTOM_CATEGORY)       # before 'Nets'


class SymbolError(ValueError):
    pass


def validate(d: dict) -> dict:
    """check and tidy a definition; raises SymbolError"""
    if not isinstance(d, dict):
        raise SymbolError('a symbol definition is a JSON object')
    name = str(d.get('name', '')).strip()
    if not NAME.match(name):
        raise SymbolError('name: 2-48 characters, lower-case letters, digits and _, starting with a letter')
    if name in REGISTRY and not REGISTRY[name].custom:
        raise SymbolError(f'{name!r} is a built-in symbol; choose another name')
    prims = d.get('prims') or []
    if not isinstance(prims, list) or not prims:
        raise SymbolError('draw at least one shape')
    out = []
    for p in prims:
        if not isinstance(p, dict) or p.get('k') not in KINDS:
            raise SymbolError(f'unknown primitive {p!r}')
        q = copy.deepcopy(p)
        if q.get('c', 'w') not in CLASSES:
            q['c'] = 'w'
        if q['k'] in ('pl', 'pg') and len(q.get('pts') or []) < 2:
            continue
        if q['k'] == 'tx':
            q.setdefault('a', 'middle'); q.setdefault('ctr', False); q['s'] = str(q.get('s', ''))
        out.append(q)
    pins = d.get('pins') or {}
    if not isinstance(pins, dict) or not pins:
        raise SymbolError('add at least one pin')
    for k, v in pins.items():
        if not re.match(r'^[\w+\-~#]{1,16}$', str(k)) or not (isinstance(v, (list, tuple)) and len(v) == 2):
            raise SymbolError(f'bad pin {k!r}')
    label = d.get('label') or {'x': 0, 'y': prim_bbox(out)[1] - 6, 'nx': 0, 'ny': -1}
    return {'name': name, 'title': str(d.get('title') or name), 'category': str(d.get('category') or CUSTOM_CATEGORY),
            'prefix': re.sub(r'[^A-Z]', '', str(d.get('prefix') or 'U').upper())[:3] or 'U',
            'prims': out, 'pins': {str(k): [float(v[0]), float(v[1])] for k, v in pins.items()}, 'label': label,
            'spice': (str(d['spice']).strip() or None) if d.get('spice') else None,
            'fields': [str(f) for f in d.get('fields') or [] if str(f).strip()], 'help': str(d.get('help') or '')}


def register(d: dict) -> Symbol:
    """add (or replace) a custom symbol from its definition"""
    d = validate(d)
    geom = G(d['prims'], d['pins'], d['label'])
    sym = Symbol(d['name'], d['title'], d['category'], lambda p, g=geom: copy.deepcopy(g), {}, d['prefix'], d['spice'],
                 help=d['help'], fields=tuple(d['fields']), custom=d)
    REGISTRY[d['name']] = sym
    try:                                     # drop cached geometry of an older version
        from .. import geometry as GEO
        for k in [k for k in GEO._geo_cache if k[0] == d['name']]:
            del GEO._geo_cache[k]
    except ImportError:
        pass
    return sym


def unregister(name: str):
    if name in REGISTRY and REGISTRY[name].custom:
        del REGISTRY[name]


def load_dir(folder) -> list:
    """register every *.json definition in a folder; returns the names (bad files are skipped)"""
    names = []
    folder = Path(folder)
    if not folder.is_dir():
        return names
    for f in sorted(folder.glob('*.json')):
        try:
            names.append(register(json.loads(f.read_text(encoding='utf-8'))).name)
        except (OSError, ValueError):
            continue
    return names


def save(folder, d: dict) -> Symbol:
    sym = register(d)
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f'{sym.name}.json').write_text(json.dumps(sym.custom, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    return sym


def used_in(doc) -> dict:
    """the custom symbols a document uses, as {name: definition}, for embedding"""
    out = {}
    for e in doc.get('elements', []):
        s = REGISTRY.get(e.get('sym')) if e.get('type') == 'comp' else None
        if s and s.custom:
            out[s.name] = s.custom
    return out


def from_builtin(name, props=None, new_name=None) -> dict:
    """a definition that starts as a copy of a built-in symbol's current drawing"""
    s = REGISTRY[name]
    g = s.geometry(props or {})
    return {'name': new_name or f'{name}_custom', 'title': f'{s.title} (custom)', 'category': CUSTOM_CATEGORY,
            'prefix': s.prefix, 'prims': copy.deepcopy(g['prims']), 'pins': copy.deepcopy(g['pins']),
            'label': copy.deepcopy(g['label']), 'spice': s.spice, 'fields': list(s.fields), 'help': ''}


def define(name, prims, pins, title=None, **kw) -> Symbol:
    """register a custom symbol from Python: define('relay_4p', prims=[...], pins={...}, title='4-pin relay')"""
    return register({'name': name, 'prims': prims, 'pins': pins, 'title': title or name, **kw})
