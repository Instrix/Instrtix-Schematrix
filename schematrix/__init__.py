"""Schematrix: electrical schematics in the Instrix house style, scriptable from Python and editable in a GUI."""
from ._cairo import borrow_app_cairo
borrow_app_cairo()                       # before anything loads cairosvg
from .document import Schematic, Comp, Pin, load
from . import netio, symbols, theme
from .render import render_svg
from .netlist import to_spice, extract as extract_netlist

__version__ = '0.2.7'
__all__ = ['Schematic', 'Comp', 'Pin', 'load', 'netio', 'symbols', 'theme', 'render_svg', 'to_spice', 'extract_netlist', 'show']


def show(*schematics):
    """mark schematics as the result of a script run in the editor"""
    for s in schematics:
        s.show()
