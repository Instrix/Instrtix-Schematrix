"""The symbol library: one module per category, all registered in REGISTRY when this package is imported.

To add a symbol, write a drawing function in the fitting category module (or a new module listed below) and
decorate it with @symbol(...); the editor, renderer, netlister and netlist importers pick it up automatically.
See core.py for the geometry conventions and helpers.
"""
from .core import (BODY, CATEGORIES, COMMON, ENUM, FLAG, FONT_SIZES, LEN, PRESETS, REGISTRY, Prop, Symbol, by_alias, catalog, get,
                   preset_for, prim_bbox, resolve, symbol, text_width)
from . import passive, semiconductor, analog, logic, digital, sources, loads, electromech, tubes, signal, generic, nets  # noqa: F401  (registration)
from .generic import parse_pins
from . import custom  # noqa: E402,F401  (user-drawn symbols)

__all__ = ['BODY', 'CATEGORIES', 'COMMON', 'ENUM', 'FLAG', 'FONT_SIZES', 'LEN', 'PRESETS', 'REGISTRY', 'Prop', 'Symbol', 'by_alias', 'catalog',
           'get', 'parse_pins', 'preset_for', 'prim_bbox', 'resolve', 'symbol', 'text_width']
