"""Text markup for every label, value and note (KiCad-style, plus named symbols).

    ~{RST}      overbar (active-low / negation)     R_{DS(on)}   subscript     x^{2}   superscript
    \\ohm \\Omega Ω   \\mu \\u µ   \\deg °   \\pm ±   \\times ×   \\le ≤  \\ge ≥  \\ne ≠  \\approx ≈  \\inf ∞  \\sqrt √
    \\alpha … \\omega and \\Alpha … \\Omega: Greek letters   \\-  a true minus sign   \\\\ \\{ \\} \\~ \\_ \\^  literals

Markers only count when a brace follows (f_c stays as typed); unknown \\names are kept as written. The same parser
lives in web/js/markup.js; keep the two in step.
"""
from __future__ import annotations

import re

GREEK = dict(alpha='α', beta='β', gamma='γ', delta='δ', epsilon='ε', zeta='ζ', eta='η', theta='θ', iota='ι', kappa='κ',
             lambda_='λ', mu='µ', nu='ν', xi='ξ', pi='π', rho='ρ', sigma='σ', tau='τ', upsilon='υ', phi='φ', chi='χ',
             psi='ψ', omega='ω', Gamma='Γ', Delta='Δ', Theta='Θ', Lambda='Λ', Xi='Ξ', Pi='Π', Sigma='Σ', Phi='Φ', Psi='Ψ',
             Omega='Ω')
SYMBOLS = {**{k.rstrip('_'): v for k, v in GREEK.items()},
           'ohm': 'Ω', 'Ohm': 'Ω', 'u': 'µ', 'micro': 'µ', 'deg': '°', 'pm': '±', 'times': '×', 'cdot': '·', 'div': '÷',
           'le': '≤', 'ge': '≥', 'ne': '≠', 'approx': '≈', 'inf': '∞', 'infty': '∞', 'sqrt': '√',
           'to': '→', 'rarrow': '→', 'larrow': '←', 'uarrow': '↑', 'darrow': '↓', 'parallel': '∥', 'angle': '∠',
           'propto': '∝', 'partial': '∂', 'int': '∫', 'sum': 'Σ', 'prod': 'Π', 'degree': '°', 'permil': '‰',
           'Re': 'ℜ', 'Im': 'ℑ', 'hbar': 'ℏ', 'bullet': '•', 'dots': '…', '-': '−'}
ESCAPES = {'\\': '\\', '{': '{', '}': '}', '~': '~', '_': '_', '^': '^', '$': '$'}
FLAGS = {'~': 'over', '_': 'sub', '^': 'sup'}


def _close(s, i):
    """index of the brace closing the one at s[i]"""
    depth = 0
    for j in range(i, len(s)):
        if s[j] == '\\':
            continue
        if s[j] == '{' and (j == 0 or s[j - 1] != '\\'):
            depth += 1
        elif s[j] == '}' and s[j - 1] != '\\':
            depth -= 1
            if depth == 0:
                return j
    return -1


def parse(s: str, flags=frozenset()) -> list:
    """-> [(text, frozenset of 'over' / 'sub' / 'sup')], adjacent runs with the same flags merged"""
    s = str(s)
    out: list = []
    buf = []

    def flush():
        if buf:
            out.append((''.join(buf), flags)); buf.clear()
    i = 0
    while i < len(s):
        c = s[i]
        if c in FLAGS and s[i + 1:i + 2] == '{':
            j = _close(s, i + 1)
            if j > 0:
                flush()
                out += parse(s[i + 2:j], flags | {FLAGS[c]})
                i = j + 1
                continue
        if c == '\\' and i + 1 < len(s):
            nxt = s[i + 1]
            if nxt in ESCAPES:
                buf.append(ESCAPES[nxt]); i += 2; continue
            if nxt == '-':
                buf.append('−'); i += 2; continue
            m = re.match(r'[A-Za-z]+', s[i + 1:])
            name = next((m.group(0)[:k] for k in range(len(m.group(0)), 0, -1) if m.group(0)[:k] in SYMBOLS), None) if m else None
            if name:                                    # longest known name: \uF -> µF, \ohm -> Ω
                buf.append(SYMBOLS[name]); i += 1 + len(name)
                if s[i:i + 2] == '{}':                  # \ohm{}k: an explicit end of the name
                    i += 2
                continue
        buf.append(c); i += 1
    flush()
    merged: list = []
    for t, f in out:
        if merged and merged[-1][1] == f:
            merged[-1] = (merged[-1][0] + t, f)
        else:
            merged.append((t, f))
    return merged


def plain(s: str) -> str:
    """the visible characters (for widths, netlists and search)"""
    return ''.join(t for t, _ in parse(s))


def svg_inner(s: str, fs: float, esc) -> str:
    """the content of an SVG <text>: plain text, or tspans for overbars and sub / superscripts"""
    runs = parse(s)
    if not runs:
        return ''
    if len(runs) == 1 and not runs[0][1]:
        return esc(runs[0][0])
    out, base = [], 0.0
    for t, f in runs:
        off = 0.32 * fs if 'sub' in f else -0.38 * fs if 'sup' in f else 0.0
        dy, base = round(off - base, 2), off
        st = ([f'font-size:{round(fs * 0.72, 2)}px'] if f & {'sub', 'sup'} else []) + (['text-decoration:overline'] if 'over' in f else [])
        attrs = (f' dy="{dy:g}"' if dy else '') + (f' style="{";".join(st)}"' if st else '')
        out.append(f'<tspan{attrs}>{esc(t)}</tspan>' if attrs else esc(t))
    return ''.join(out)


def has_markup(s: str) -> bool:
    return bool(re.search(r'[~_^]\{|\\', str(s)))


def width_chars(s: str) -> float:
    """visible length in characters, sub / superscripts counting at their smaller size"""
    return sum(len(t) * (0.72 if f & {'sub', 'sup'} else 1) for t, f in parse(s))
