"""The symbol library: one module per category, all registered in REGISTRY when this package is imported.

To add a symbol, write a drawing function in the fitting category module (or a new module listed below) and
decorate it with @symbol(...); the editor, renderer, netlister and netlist importers pick it up automatically.
See core.py for the geometry conventions and helpers.
"""
from .core import (BODY, CATEGORIES, COMMON, ENUM, FLAG, FONT_SIZES, LEN, REGISTRY, Prop, Symbol, catalog, get,
                   prim_bbox, symbol, text_width)
from . import passive, semiconductor, analog, logic, sources, loads, electromech, tubes, signal, generic, nets  # noqa: F401  (registration)
from .generic import parse_pins

__all__ = ['BODY', 'CATEGORIES', 'COMMON', 'ENUM', 'FLAG', 'FONT_SIZES', 'LEN', 'REGISTRY', 'Prop', 'Symbol', 'catalog',
           'get', 'parse_pins', 'prim_bbox', 'symbol', 'text_width']
