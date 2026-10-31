"""Text as outlines for Cairo: PDF, EPS and PNG made by the server, the CLI and Python look the same everywhere.

cairosvg draws text with the fonts installed on the computer; where JetBrains Mono or Inter are missing it
substitutes another font, or draws empty boxes for characters like − √ → eₙ. This turns every text set in one of
the bundled fonts into vector paths drawn from the font files that ship with Schematrix, so nothing depends on
the computer's fonts. Texts in other fonts (the formal, technical and kicad themes use system fonts) stay text.

Styles come from the SVG's own <style> block, so any theme, custom theme or raw legacy markup is handled.
Needs fontTools and brotli (the bundled fonts are WOFF2); without them the SVG is returned unchanged.
"""
from __future__ import annotations

import functools
import math
import os
import re
import xml.etree.ElementTree as ET

from . import theme as TH

NS = 'http://www.w3.org/2000/svg'
BUNDLED = {'jetbrains mono': 'JetBrains Mono', 'inter': 'Inter'}
FALLBACK = {'JetBrains Mono': 'Inter', 'Inter': 'JetBrains Mono'}     # for characters a font lacks (ₙ in Mono)
ITALIC_SKEW = math.tan(math.radians(10))                               # synthetic italic where no italic face exists


def available() -> bool:
    try:
        import brotli  # noqa: F401  (WOFF2)
        from fontTools.ttLib import TTFont  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


# ---------------------------------------------------------------- fonts
@functools.lru_cache(maxsize=None)
def _font(path):
    from fontTools.ttLib import TTFont
    f = TTFont(path)
    return f.getBestCmap(), f.getGlyphSet(), f['hmtx'].metrics, f['head'].unitsPerEm


@functools.lru_cache(maxsize=None)
def _faces(family, weight, italic):
    """the font files (every subset) closest to a family / weight / style, and whether the italic is real"""
    faces = [(w, st, stem) for fam, w, st, stem in TH._FACES if fam == family]
    want = 'italic' if italic else 'normal'
    styled = [f for f in faces if f[1] == want] or [f for f in faces if f[1] == 'normal']
    w, st, stem = min(styled, key=lambda f: abs(f[0] - weight))
    paths = [os.path.join(TH.FONT_DIR, stem.format(s=sub) + '.woff2') for sub in TH._RANGES]
    return [p for p in paths if os.path.exists(p)], st == want


def _glyph(ch, family, weight, italic):
    """(glyph set, glyph name, advance, units per em, synthetic italic) for a character, with fallbacks"""
    for fam in (family, FALLBACK[family]):
        paths, real = _faces(fam, weight, italic)
        for p in paths:
            cmap, gs, hmtx, upem = _font(p)
            name = cmap.get(ord(ch))
            if name is not None:
                return gs, name, hmtx[name][0], upem, italic and not real
    return None


# ---------------------------------------------------------------- styles
def _rules(svg_root):
    """simple CSS rules of the SVG's <style>: [(selector, {prop: value})], in order"""
    css = ''.join(el.text or '' for el in svg_root.iter(f'{{{NS}}}style'))
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    out = []
    for sels, body in re.findall(r'([^{}]+)\{([^{}]*)\}', css):
        decl = dict((k.strip().lower(), v.strip()) for k, v in
                    (d.split(':', 1) for d in body.split(';') if ':' in d))
        for sel in sels.split(','):
            sel = sel.strip()
            if sel and not sel.startswith('@'):
                out.append((sel, decl))
    return out


def _style(el, rules, inherited):
    st = dict(inherited)
    classes = (el.get('class') or '').split()
    tag = el.tag.split('}')[-1]
    for sel, decl in rules:
        if sel == tag or (sel.startswith('.') and '.' not in sel[1:] and ' ' not in sel and sel[1:] in classes):
            st.update(decl)
    for k in ('fill', 'font-family', 'font-size', 'font-weight', 'font-style', 'letter-spacing', 'text-anchor'):
        if el.get(k):
            st[k] = el.get(k)
    for d in (el.get('style') or '').split(';'):
        if ':' in d:
            k, v = d.split(':', 1)
            st[k.strip().lower()] = v.strip()
    return st


def _px(v, fs=12.0, default=0.0):
    v = (v or '').strip()
    try:
        if v.endswith('em'):
            return float(v[:-2]) * fs
        return float(v.rstrip('px') or default)
    except ValueError:
        return default


def _weight(v):
    v = (v or '400').strip().lower()
    try:
        return {'normal': 400, 'bold': 700, 'bolder': 700, 'lighter': 300}.get(v) or int(float(v))
    except ValueError:
        return 400


def _family(v):
    first = (v or '').split(',')[0].strip().strip('"\'').lower()
    return BUNDLED.get(first)


# ---------------------------------------------------------------- text -> paths
def _runs(el):
    """(text, font-size override, baseline offset, overline, style dict of the tspan) in order"""
    out, base = [(el.text or '', None, 0.0, False, None)], 0.0
    for c in el:
        base += _px(c.get('dy'))
        st = c.get('style') or ''
        sm = re.search(r'font-size:\s*([\d.]+)px', st)
        out.append((c.text or '', float(sm.group(1)) if sm else None, base, 'overline' in st, c))
        out.append((c.tail or '', None, base, False, None))
    return out


def _outline_text(el, st):
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    family = _family(st.get('font-family'))
    fs = _px(st.get('font-size'), default=12.0) or 12.0
    weight, italic = _weight(st.get('font-weight')), (st.get('font-style') or '').strip() in ('italic', 'oblique')
    ls = _px(st.get('letter-spacing'), fs)
    fill = st.get('fill') or '#000'
    pieces, bars, x = [], [], 0.0
    for text, size, dy, over, _ in _runs(el):
        size = size or fs
        x0 = x
        for ch in text:
            g = _glyph(ch, family, weight, italic)
            if g is None:
                x += 0.6 * size + ls
                continue
            gs, name, adv, upem, synth = g
            s = size / upem
            pieces.append((gs, name, (s, 0, s * ITALIC_SKEW if synth else 0, -s, x, dy)))
            x += adv * s + ls
        if over and x > x0:
            bars.append((x0 + fs * 0.04, x - ls - fs * 0.04))
    x_start = float(el.get('x', 0) or 0) - {'start': 0, 'middle': x / 2, 'end': x}.get(st.get('text-anchor', 'start'), 0)
    y = float(el.get('y', 0) or 0)
    cmds = []
    for gs, name, (a, b, c, d, e, f) in pieces:
        pen = SVGPathPen(gs)              # the glyph set resolves composite glyphs (accented letters)
        gs[name].draw(TransformPen(pen, (a, b, c, d, e + x_start, f + y)))
        cmds.append(pen.getCommands())
    g = ET.Element(f'{{{NS}}}g', {'class': 'txt'})
    for k in ('transform', 'opacity'):
        if el.get(k):
            g.set(k, el.get(k))
    d = ' '.join(c for c in cmds if c)
    if d:
        ET.SubElement(g, f'{{{NS}}}path', {'d': d, 'fill': fill})
    yb = y - fs * 0.8
    for a, b in bars:
        ET.SubElement(g, f'{{{NS}}}line', {'x1': f'{x_start + a:.2f}', 'x2': f'{x_start + b:.2f}', 'y1': f'{yb:.2f}',
                                           'y2': f'{yb:.2f}', 'stroke': fill, 'stroke-width': f'{max(0.6, fs * 0.065):.2f}'})
    return g


def outline(svg: str) -> str:
    """every text in a bundled font -> paths; other texts are left alone"""
    if '<text' not in svg or not available():
        return svg
    ET.register_namespace('', NS)
    root = ET.fromstring(svg)
    rules = _rules(root)

    def walk(parent, inherited):
        for i, el in enumerate(list(parent)):
            tag = el.tag.split('}')[-1]
            if tag in ('style', 'defs'):
                continue
            st = _style(el, rules, inherited)
            if tag == 'text':
                if _family(st.get('font-family')):
                    parent.remove(el)
                    parent.insert(i, _outline_text(el, st))
            elif len(el):
                walk(el, {k: v for k, v in st.items() if k in ('fill', 'font-family', 'font-size', 'font-weight',
                                                                 'font-style', 'letter-spacing', 'text-anchor')})
    walk(root, {})
    return ET.tostring(root, encoding='unicode')
