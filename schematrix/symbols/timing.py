"""Timing diagrams from a WaveDrom-like description, one signal per line:

    CLK  : p.......
    EN   : 0..1....|..0
    DATA : x.=.=.x. | A5 3C        (labels for = and 2..9 cells after a bar)

Wave characters: p / n clock (rising / falling edge first), 0 1 low / high, z high impedance, x unknown,
= and 2..9 data cells (2..9 shaded), . extends the previous state, | marks a gap in time. An empty line leaves a
space. Names and labels take text markup and $...$ maths.
"""
from __future__ import annotations

from .core import FLAG, G, Prop, pg, pl, symbol, tx

SLOPE = 3.0              # width of a level change (clock edges are vertical)
DATA = set('=23456789x')


def parse(text: str) -> list:
    """-> [(name, wave, [labels]) or None for a spacer]"""
    rows = []
    for line in str(text or '').splitlines():
        if not line.strip():
            rows.append(None)
            continue
        name, _, rest = line.partition(':') if ':' in line else ('', '', line)
        wave, _, labels = rest.partition(' | ') if ' | ' in rest else (rest, '', '')
        rows.append((name.strip(), wave.strip().replace(' ', ''), labels.split()))
    return rows


def _cells(wave):
    """wave string -> [(char, start, length, gap_after)] with '.' merged into the cell before it"""
    out = []
    for c in wave:
        if c == '|':
            if out:
                out[-1][3].append(out[-1][1] + out[-1][2])
            continue
        if c == '.' and out:
            out[-1][2] += 1
        else:
            out.append([c if c != '.' else 'x', len(out) and out[-1][1] + out[-1][2], 1, []])
    return out


def _row(wave, labels, step, A):
    """the prims of one waveform, origin at its left / centre"""
    prims, lvl = [], []          # lvl: the running polyline of 0 / 1 / z / clock levels
    level = {'0': A, 'l': A, '1': -A, 'h': -A, 'z': 0, 'u': -A, 'd': A}
    cells = _cells(wave)
    li = 0

    def flush():
        if len(lvl) > 1:
            prims.append(pl(list(lvl), 'w'))
        lvl.clear()
    for i, (c, s, n, gaps) in enumerate(cells):
        x0, x1 = s * step, (s + n) * step
        prev = cells[i - 1][0] if i else None
        nxt = cells[i + 1][0] if i + 1 < len(cells) else None
        if c in 'pnPN':
            hi_first = c in 'pP'
            for k in range(n):
                a, m, b = x0 + k * step, x0 + k * step + step / 2, x0 + (k + 1) * step
                y1, y2 = (-A, A) if hi_first else (A, -A)
                if not lvl:
                    lvl.append((a, y1))
                elif lvl[-1][1] != y1:
                    lvl.append((a, y1))
                lvl += [(m, y1), (m, y2), (b, y2)]
        elif c in level:
            y = level[c]
            if not lvl:
                lvl.append((x0, y))
            elif lvl[-1][1] != y:                     # a slanted change centred on the cell boundary
                lvl[-1] = (x0 - SLOPE / 2, lvl[-1][1])
                lvl.append((x0 + SLOPE / 2, y))
            lvl.append((x1, y))
        else:                                           # a data / unknown cell: a hexagon between its neighbours
            yl = level.get(prev, 0) if prev and prev not in DATA and prev not in 'pnPN' else 0
            yr = level.get(nxt, 0) if nxt and nxt not in DATA and nxt not in 'pnPN' else 0
            if lvl:
                lvl[-1] = (x0, lvl[-1][1])
                flush()
            h = SLOPE
            cls = 'tx' if c == 'x' else 'tdata' if c == '=' else 'tdata2'
            prims.append(pg([(x0, yl), (x0 + h, -A), (x1 - h, -A), (x1, yr), (x1 - h, A), (x0 + h, A)], cls))
            if c != 'x':
                label = labels[li] if li < len(labels) else ''
                li += 1
                if label:
                    prims.append(tx((x0 + x1) / 2, 0, label, 'valsm', ctr=True, fit=x1 - x0 - 2 * h - 2))
            if nxt and nxt in level:
                lvl.append((x1, yr))
        for g in gaps:                                  # a gap: two slanted strokes across the row
            gx = g * step
            prims += [pg([(gx - 4, A + 3), (gx, -A - 3), (gx + 4, -A - 3), (gx, A + 3)], 'gap'),
                      pl([(gx - 4, A + 3), (gx, -A - 3)], 'w thin'), pl([(gx, A + 3), (gx + 4, -A - 3)], 'w thin')]
    flush()
    return prims, sum(n for _, _, n, _ in cells)


@symbol('timing', 'Timing diagram', 'Annotation', 'TD', None,
        {'signals': Prop('CLK : p.......\nEN  : 0.1.....0.\nDATA: x..=.=..x | A5 3C', 'text', True, label='Signals',
                         help='NAME : wave | labels, one per line. p n clock, 0 1 level, z, x, = 2..9 data, . extend, | gap'),
         'step': Prop(24, 'num', True, label='Cycle width'), 'row': Prop(30, 'num', True, label='Row pitch'),
         'height': Prop(14, 'num', True, label='Signal height'), 'grid': FLAG(False, 'Cycle grid'),
         'title': Prop('', 'str', label='Title')},
        lines=(('title', 'lbl'),), help='timing / waveform diagram from a WaveDrom-like description')
def timing(p):
    step, row = max(4.0, float(p.get('step') or 24)), max(8.0, float(p.get('row') or 30))
    A = max(2.0, float(p.get('height') or 14)) / 2
    rows = parse(p.get('signals'))
    prims, width = [], 0
    for i, r in enumerate(rows):
        if not r:
            continue
        y = i * row + row / 2
        name, wave, labels = r
        rp, cycles = _row(wave, labels, step, A)
        width = max(width, cycles * step)
        prims += [{**q, 'pts': [[a, b + y] for a, b in q['pts']]} if 'pts' in q else {**q, 'y': q['y'] + y} for q in rp]
        if name:
            prims.append(tx(-10, y, name, 'lbl', 'end', ctr=True))
    if p.get('grid'):
        n = int(round(width / step))
        prims[:0] = [pl([(k * step, 0), (k * step, len(rows) * row)], 'grid') for k in range(n + 1)]
    return G(prims, {}, {'x': width / 2, 'y': -8, 'nx': 0, 'ny': -1})       # a title centred over the waves
