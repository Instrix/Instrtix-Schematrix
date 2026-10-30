"""Themes: colour tokens, fonts and the drawing CSS shared by the Python renderer and the web editor.

The default theme is the Instrix brand palette from the original TR-0002 figures. A document can name a theme
("instrix", "instrix-dark", "blueprint", "print-mono") or carry a dict that overrides any token of the default.
"""
from __future__ import annotations

import base64
import functools
import os

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web', 'fonts')

THEMES: dict[str, dict[str, str]] = {
    'instrix': dict(ink='#292b31', muted='#545866', rule='#d3d6df', surface='#eef0f4', accent='#23699f',
                    paper='#ffffff', accent_fill='#dbe8f3',
                    mono='"JetBrains Mono", ui-monospace, monospace', sans='"Inter", system-ui, sans-serif'),
    'instrix-dark': dict(ink='#e4e6ec', muted='#9ba1af', rule='#3a3e48', surface='#252931', accent='#62a8e0',
                         paper='#16181d', accent_fill='#1d3346',
                         mono='"JetBrains Mono", ui-monospace, monospace', sans='"Inter", system-ui, sans-serif'),
    'blueprint': dict(ink='#eaf2ff', muted='#a9c3e8', rule='#3d6aa8', surface='#1f4d8c', accent='#ffd166',
                      paper='#16407a', accent_fill='#2a5a9a',
                      mono='"JetBrains Mono", ui-monospace, monospace', sans='"Inter", system-ui, sans-serif'),
    'print-mono': dict(ink='#000000', muted='#333333', rule='#bbbbbb', surface='#f2f2f2', accent='#000000',
                       paper='#ffffff', accent_fill='#e6e6e6',
                       mono='"JetBrains Mono", ui-monospace, monospace', sans='"Inter", system-ui, sans-serif'),
}
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
    return base


def css(theme=None) -> str:
    t = resolve(theme)
    return f"""
.w {{ fill: none; stroke: {t['ink']}; stroke-width: 1.5; stroke-linejoin: round; stroke-linecap: round; }}
.plate {{ stroke-width: 2.2; }}
.bus {{ stroke-width: 3.4; }}
.acc {{ stroke: {t['accent']}; stroke-width: 2.2; }}
.para {{ stroke-dasharray: 5 3; }}
.rule {{ stroke-dasharray: 2 4; }}
.thin {{ stroke-width: 1; }}
.accf {{ fill: {t['accent']}; }}
.dot, .arrow {{ fill: {t['ink']}; }}
.acc.arrow, .acc.dot {{ fill: {t['accent']}; stroke: none; }}
.amp {{ fill: {t['paper']}; stroke: {t['ink']}; stroke-width: 1.6; }}
.amp.acc {{ stroke: {t['accent']}; }}
.pad {{ fill: {t['paper']}; stroke: {t['ink']}; stroke-width: 1.4; }}
.term {{ fill: {t['paper']}; stroke: {t['ink']}; stroke-width: 1.8; }}
.flag {{ fill: {t['surface']}; stroke: {t['ink']}; stroke-width: 1.2; }}
.box {{ fill: {t['surface']}; stroke: {t['ink']}; stroke-width: 1.6; }}
.accbox {{ fill: {t['accent_fill']}; stroke: {t['ink']}; stroke-width: 1.6; }}
.grp {{ fill: {t['surface']}; stroke: none; }}
.frame {{ fill: none; stroke: {t['rule']}; stroke-width: 1.2; }}
text {{ font-family: {t['mono']}; fill: {t['ink']}; }}
.lbl, .ref {{ font-size: 12px; font-weight: 500; }}
.val {{ font-size: 11.5px; fill: {t['muted']}; }}
.valsm {{ font-size: 10.5px; fill: {t['muted']}; }}
.node {{ font-size: 12px; font-weight: 500; font-style: italic; }}
.net {{ font-size: 11px; font-weight: 500; }}
.pin {{ font-size: 13px; font-weight: 600; }}
.termlbl {{ font-size: 12.5px; font-weight: 600; }}
.accl {{ font-size: 12px; font-weight: 600; fill: {t['accent']}; }}
.grplbl {{ font-size: 10px; font-weight: 600; letter-spacing: .08em; fill: {t['muted']}; }}
.note {{ font-family: {t['sans']}; font-size: 12px; fill: {t['muted']}; }}
.title {{ font-family: {t['sans']}; font-size: 15px; font-weight: 600; }}
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
