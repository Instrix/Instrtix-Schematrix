"""Text markup for every label, value and note (KiCad-style, plus named symbols).

    ~{RST}      overbar (active-low / negation)     R_{DS(on)}   subscript     x^{2}   superscript
    \\ohm \\Omega Ω   \\mu \\u µ   \\deg °   \\pm ±   \\times ×   \\le ≤  \\ge ≥  \\ne ≠  \\approx ≈  \\inf ∞  \\sqrt √
    \\alpha … \\omega and \\Alpha … \\Omega: Greek letters   \\-  a true minus sign   \\\\ \\{ \\} \\~ \\_ \\^  literals

    $...$       LaTeX maths: V_{out} = \\frac{R_2}{R_1} V_{in}, \\sqrt{2}, \\overline{Q}: drawn with the markup above
                (fractions as a/b), and exported to TikZ as real LaTeX maths. \\$ is a literal dollar.

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


MATH_TEXT = {'mathrm', 'text', 'mathit', 'mathbf', 'mathsf', 'mathtt', 'textrm', 'textit', 'textbf', 'mbox',
             'operatorname', 'mathcal', 'boldsymbol'}
MATH_SPACE = {',': ' ', ';': ' ', ':': ' ', '!': '', ' ': ' ', 'quad': '  ', 'qquad': '   '}
MATH_DROP = {'left', 'right', 'big', 'Big', 'bigl', 'bigr', 'Bigl', 'Bigr', 'displaystyle', 'textstyle', 'limits'}
MATH_SYMBOLS = {'ldots': '…', 'cdots': '⋯', 'leq': '≤', 'geq': '≥', 'neq': '≠', 'rightarrow': '→', 'leftarrow': '←',
                'varphi': 'φ', 'varepsilon': 'ε', 'ell': 'ℓ', 'sim': '∼', 'mp': '∓', 'circ': '°', 'prime': '′'}


def _math_arg(t, i):
    """the argument at t[i] (after spaces): a {group}, a \\command or one character -> (text, next index)"""
    while i < len(t) and t[i] == ' ':
        i += 1
    if i >= len(t):
        return '', i
    if t[i] == '{':
        depth = 0
        for j in range(i, len(t)):
            if t[j] == '\\':
                continue
            if t[j] == '{' and t[j - 1] != '\\':
                depth += 1
            elif t[j] == '}' and t[j - 1] != '\\':
                depth -= 1
                if depth == 0:
                    return t[i + 1:j], j + 1
        return t[i + 1:], len(t)
    if t[i] == '\\':
        m = re.match(r'\\([A-Za-z]+|.)', t[i:])
        return m.group(0), i + len(m.group(0))
    return t[i], i + 1


def _paren(s):
    """brackets around a fraction's part when it is more than one term (R_{2} stays bare, 2\\pi RC gets them)"""
    terms = re.findall(r'(?:\d+(?:\.\d+)?|\\[A-Za-z]+\{\}|[^\s_^~{}])(?:[_^]\{[^{}]*\})*', s)
    return f'({s})' if len(terms) > 1 and not (s.startswith('(') and s.endswith(')')) else s


MATH_REL = {'=': '=', '<': '<', '>': '>', 'approx': '≈', 'le': '≤', 'ge': '≥', 'ne': '≠', 'leq': '≤', 'geq': '≥',
            'neq': '≠', 'sim': '∼', 'to': '→', 'rightarrow': '→', 'leftarrow': '←', 'propto': '∝'}
MATH_BIN = {'+': '+', '-': '−', 'pm': '±', 'mp': '∓', 'times': '×', 'cdot': '·', 'div': '÷'}


def math_markup(t: str, text=False) -> str:
    """LaTeX maths -> this markup, for drawing (fractions become a/b). Like TeX, spaces in the source are ignored and
    relations / binary operators get spaces of their own (a leading minus stays unary)."""
    out, i = [], 0

    def op(sym, rel):
        prev = ''.join(out).rstrip()
        if rel and prev or prev and prev[-1] not in '(=<>≈≤≥≠∼→←∝+−±∓×·÷,':
            out[:] = [prev, f' {sym} ']
        else:
            out.append(sym)                             # unary: -x, = -x
    while i < len(t):
        c = t[i]
        if c == ' ' and not text:
            i += 1; continue
        if not text and (c in MATH_REL or c in MATH_BIN):
            op(MATH_REL.get(c) or MATH_BIN[c], c in MATH_REL); i += 1; continue
        if c == ',' and not text:
            out.append(', '); i += 1; continue
        if c == '\\':
            m = re.match(r'[A-Za-z]+|.', t[i + 1:])
            name = m.group(0) if m else ''
            i += 1 + len(name)
            if name in MATH_SPACE:
                out.append(MATH_SPACE[name])
            elif name in MATH_DROP:
                pass
            elif name in MATH_REL or name in MATH_BIN:
                op(MATH_REL.get(name) or MATH_BIN[name], name in MATH_REL)
            elif name in MATH_TEXT:
                a, i = _math_arg(t, i); out.append(math_markup(a, text=name.startswith('text') or name == 'mbox'))
            elif name in ('frac', 'dfrac', 'tfrac'):
                a, i = _math_arg(t, i); b, i = _math_arg(t, i)
                out.append(f'{_paren(math_markup(a))}/{_paren(math_markup(b))}\u2009')    # thin space before what follows
            elif name == 'sqrt':
                a, i = _math_arg(t, i); out.append('√' + _paren(math_markup(a)))
            elif name in ('overline', 'bar'):
                a, i = _math_arg(t, i); out.append('~{' + math_markup(a) + '}')
            elif name in MATH_SYMBOLS:
                out.append(MATH_SYMBOLS[name])
            elif name in SYMBOLS:
                out.append('\\' + name + '{}')
            elif name in ESCAPES or name in '%&#':
                out.append('\\' + name if name in ESCAPES else name)
            else:
                out.append(name)                        # \\sin, \\log, \\max: the name itself
            continue
        if c in '_^':
            a, i = _math_arg(t, i + 1); out.append(c + '{' + math_markup(a) + '}'); continue
        if c == '{':
            a, i = _math_arg(t, i); out.append(math_markup(a)); continue
        out.append({'~': ' ', '}': ''}.get(c, c)); i += 1
    s = ''.join(out)
    return s if text else s.strip()


def _math_end(s, i):
    """index of the $ closing the one at s[i], or -1"""
    j = i + 1
    while j < len(s):
        if s[j] == '\\':
            j += 2; continue
        if s[j] == '$':
            return j if j > i + 1 else -1
        j += 1
    return -1


def has_math(s: str) -> bool:
    s = str(s)
    return any(c == '$' and (i == 0 or s[i - 1] != '\\') and _math_end(s, i) > 0 for i, c in enumerate(s))


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
        if c == '$':
            j = _math_end(s, i)
            if j > 0:
                flush()
                out += parse(math_markup(s[i + 1:j]), flags)
                i = j + 1
                continue
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
    return bool(re.search(r'[~_^]\{|\\', str(s))) or has_math(s)


def to_latex(s: str, esc) -> str:
    """the whole label as LaTeX: maths passes through as $...$, the rest is escaped with esc and its markup becomes
    \\overline / \\textsubscript / \\textsuperscript"""
    s, out, i, seg = str(s), [], 0, 0
    while i < len(s):
        if s[i] == '\\':
            i += 2; continue
        if s[i] == '$' and _math_end(s, i) > 0:
            j = _math_end(s, i)
            out.append(_text_latex(s[seg:i], esc)); out.append('$' + s[i + 1:j] + '$')
            i = seg = j + 1; continue
        i += 1
    out.append(_text_latex(s[seg:], esc))
    return ''.join(out)


def _text_latex(s, esc):
    out = []
    for t, f in parse(s):
        body = esc(t)
        if 'over' in f:
            body = f'\\ensuremath{{\\overline{{\\mbox{{{body}}}}}}}'
        if 'sub' in f:
            body = f'\\textsubscript{{{body}}}'
        elif 'sup' in f:
            body = f'\\textsuperscript{{{body}}}'
        out.append(body)
    return ''.join(out)


def width_chars(s: str) -> float:
    """visible length in characters, sub / superscripts counting at their smaller size"""
    return sum(len(t) * (0.72 if f & {'sub', 'sup'} else 1) for t, f in parse(s))
