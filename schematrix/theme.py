"""Themes: colour tokens, fonts and the drawing CSS shared by the Python renderer and the web editor.

The default theme is the Instrix brand palette, the Instrix documentation look. A document can name a theme
("instrix", "instrix-dark", "blueprint", "print-mono", "formal", "technical", "kicad") or carry a dict that
overrides any token of the default.
"""
from __future__ import annotations

import base64
import functools
import os

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web', 'fonts')

MONO = '"JetBrains Mono", ui-monospace, monospace'
SANS = '"Inter", system-ui, sans-serif'
# Times-like faces with Greek first: cairosvg (PDF / EPS) uses only the first installed family, no per-glyph fallback
SERIF = ('"Times New Roman", "Liberation Serif", "TeX Gyre Termes", "Nimbus Roman", Times, "Latin Modern Roman", '
         '"CMU Serif", serif')
HELV = '"Helvetica Neue", Helvetica, Arial, "Nimbus Sans", "Liberation Sans", sans-serif'

THEMES: dict[str, dict[str, str]] = {
    'instrix': dict(ink='#292b31', muted='#545866', rule='#d3d6df', surface='#eef0f4', accent='#23699f',
                    paper='#ffffff', accent_fill='#dbe8f3', mono=MONO, sans=SANS),
    'instrix-dark': dict(ink='#e4e6ec', muted='#9ba1af', rule='#3a3e48', surface='#252931', accent='#62a8e0',
                         paper='#16181d', accent_fill='#1d3346', mono=MONO, sans=SANS),
    'blueprint': dict(ink='#eaf2ff', muted='#a9c3e8', rule='#3d6aa8', surface='#1f4d8c', accent='#ffd166',
                      paper='#16407a', accent_fill='#2a5a9a', mono=MONO, sans=SANS),
    'print-mono': dict(ink='#000000', muted='#333333', rule='#bbbbbb', surface='#f2f2f2', accent='#000000',
                       paper='#ffffff', accent_fill='#e6e6e6', mono=MONO, sans=SANS),
    # for papers and theses typeset in LaTeX / Times: serif text, black, thin even lines, italic references
    'formal': dict(ink='#000000', muted='#000000', rule='#9a9a9a', surface='#f0f0f0', accent='#000000',
                   paper='#ffffff', accent_fill='#e8e8e8', box='#ffffff', mono=SERIF, sans=SERIF,
                   lw='1', lw_plate='1.7', lw_thin='0.7', lw_body='1.1', lw_bus='2.6', weight='400', strong='400',
                   ref_style='italic', join='miter'),
    # datasheet / IEEE look: Helvetica, black, medium lines, upright text
    'technical': dict(ink='#000000', muted='#222222', rule='#b0b0b0', surface='#f3f3f3', accent='#0050a0',
                      paper='#ffffff', accent_fill='#e3edf7', box='#ffffff', mono=HELV, sans=HELV,
                      lw='1.25', lw_plate='2', lw_thin='0.8', lw_body='1.3', lw_bus='3', weight='400', strong='600',
                      join='miter'),
    # KiCad's classic Eeschema colours: dark red symbols with pale yellow bodies, green wires and junctions
    'kicad': dict(ink='#840000', muted='#006464', rule='#c8c8c8', surface='#ffffc2', accent='#c80000',
                  paper='#f5f4ef', accent_fill='#ffe4b5', box='#ffffc2', body='#ffffc2', wire='#008400', text='#006464',
                  mono='"KiCad Font", "Liberation Sans", Arial, sans-serif', sans='"Liberation Sans", Arial, sans-serif',
                  lw='1.2', lw_plate='2', lw_thin='0.8', lw_body='1.4', lw_bus='3.4', weight='400', strong='600'),
}
# tokens a theme may leave out
DEFAULTS = dict(lw='1.5', lw_plate='2.2', lw_thin='1', lw_body='1.6', lw_bus='3.4', weight='500', strong='600',
                ref_style='normal', join='round')
DEFAULT_THEME = 'instrix'

# text classes a free text element may use, with a human description (the editor lists these)
TEXT_CLASSES = {
    'lbl': 'Label', 'ref': 'Reference', 'val': 'Value', 'valsm': 'Small value', 'node': 'Node name (italic)',
    'net': 'Net', 'pin': 'Pin sign', 'termlbl': 'Terminal', 'accl': 'Accent label', 'grplbl': 'Group label',
    'note': 'Note (sans)', 'title': 'Title',
}


def resolve(theme) -> dict[str, str]:
    """theme name or override dict -> full token dict"""
    base = dict(THEMES[DEFAULT_THEME])
    if isinstance(theme, str):
        base.update(THEMES.get(theme, {}))
    elif isinstance(theme, dict):
        if isinstance(theme.get('base'), str):
            base.update(THEMES.get(theme['base'], {}))
        base.update({k: v for k, v in theme.items() if k != 'base'})
    for k, v in DEFAULTS.items():
        base.setdefault(k, v)
    base.setdefault('wire', base['ink'])          # wires may differ from symbol lines (kicad)
    base.setdefault('text', base['ink'])
    base.setdefault('box', base['surface'])       # block / box fill
    base.setdefault('body', base['paper'])        # op-amp, source and gate bodies
    return base


def css(theme=None) -> str:
    t = resolve(theme)
    cap = 'round' if t['join'] == 'round' else 'butt'
    return f"""
.w {{ fill: none; stroke: {t['ink']}; stroke-width: {t['lw']}; stroke-linejoin: {t['join']}; stroke-linecap: {cap}; }}
.wire {{ stroke: {t['wire']}; }}
.plate {{ stroke-width: {t['lw_plate']}; }}
.bus {{ stroke-width: {t['lw_bus']}; }}
.acc {{ stroke: {t['accent']}; stroke-width: {t['lw_plate']}; }}
.para {{ stroke-dasharray: 5 3; }}
.rule {{ stroke-dasharray: 2 4; }}
.thin {{ stroke-width: {t['lw_thin']}; }}
.accf {{ fill: {t['accent']}; }}
.dot, .arrow {{ fill: {t['ink']}; }}
.jn {{ fill: {t['wire']}; }}
.acc.arrow, .acc.dot {{ fill: {t['accent']}; stroke: none; }}
.amp {{ fill: {t['body']}; stroke: {t['ink']}; stroke-width: {t['lw_body']}; }}
.amp.acc {{ stroke: {t['accent']}; }}
.pad {{ fill: {t['paper']}; stroke: {t['ink']}; stroke-width: {t['lw_thin']}; }}
.term {{ fill: {t['paper']}; stroke: {t['ink']}; stroke-width: {t['lw_plate']}; }}
.flag {{ fill: {t['surface']}; stroke: {t['ink']}; stroke-width: {t['lw_thin']}; }}
.box {{ fill: {t['box']}; stroke: {t['ink']}; stroke-width: {t['lw_body']}; }}
.accbox {{ fill: {t['accent_fill']}; stroke: {t['ink']}; stroke-width: {t['lw_body']}; }}
.grp {{ fill: {t['surface']}; stroke: none; }}
.frame {{ fill: none; stroke: {t['rule']}; stroke-width: {t['lw_thin']}; }}
text {{ font-family: {t['mono']}; fill: {t['text']}; }}
.lbl, .ref {{ font-size: 12px; font-weight: {t['weight']}; }}
.ref {{ font-style: {t['ref_style']}; }}
.val {{ font-size: 11.5px; fill: {t['muted']}; }}
.valsm {{ font-size: 10.5px; fill: {t['muted']}; }}
.node {{ font-size: 12px; font-weight: {t['weight']}; font-style: italic; }}
.net {{ font-size: 11px; font-weight: {t['weight']}; }}
.pin {{ font-size: 13px; font-weight: {t['strong']}; }}
.termlbl {{ font-size: 12.5px; font-weight: {t['strong']}; }}
.accl {{ font-size: 12px; font-weight: {t['strong']}; fill: {t['accent']}; font-style: {t['ref_style']}; }}
.grplbl {{ font-size: 10px; font-weight: {t['strong']}; letter-spacing: .08em; fill: {t['muted']}; }}
.note {{ font-family: {t['sans']}; font-size: 12px; fill: {t['muted']}; }}
.title {{ font-family: {t['sans']}; font-size: 15px; font-weight: {t['strong']}; }}
"""


_FACES = [  # (family, weight, style, subset file stem)
    ('JetBrains Mono', 400, 'normal', 'jetbrains-mono-{s}-400-normal'),
    ('JetBrains Mono', 500, 'normal', 'jetbrains-mono-{s}-500-normal'),
    ('JetBrains Mono', 600, 'normal', 'jetbrains-mono-{s}-600-normal'),
    ('JetBrains Mono', 500, 'italic', 'jetbrains-mono-{s}-500-italic'),
    ('Inter', 400, 'normal', 'inter-{s}-400-normal'),
    ('Inter', 500, 'normal', 'inter-{s}-500-normal'),
    ('Inter', 600, 'normal', 'inter-{s}-600-normal'),
]
_RANGES = {'latin': 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+20AC,U+2122,'
                    'U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD',
           'greek': 'U+0370-03FF'}


@functools.lru_cache(maxsize=4)
def font_faces(embed: bool = True, url_prefix: str = '/static/fonts/') -> str:
    """@font-face rules for the bundled fonts, either embedded as base64 (portable SVG) or as URLs"""
    out = []
    for fam, w, st, stem in _FACES:
        for sub, rng in _RANGES.items():
            fn = stem.format(s=sub) + '.woff2'
            path = os.path.join(FONT_DIR, fn)
            if not os.path.exists(path):
                continue
            if embed:
                with open(path, 'rb') as f:
                    src = 'data:font/woff2;base64,' + base64.b64encode(f.read()).decode()
            else:
                src = url_prefix + fn
            out.append(f'@font-face {{ font-family: "{fam}"; font-weight: {w}; font-style: {st}; '
                       f'src: url({src}) format("woff2"); unicode-range: {rng}; }}')
    return '\n'.join(out)
