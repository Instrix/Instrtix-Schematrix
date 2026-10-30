#!/usr/bin/env python3
"""Schematics for TR-0002 (Instrix-Docs registry), as standalone SVGs. Run from this folder: python3 schematics.py

Drawn from the netlist in ../Filters/Simulations/afe1_ladder_x10/gen_decks.py (RANGES=6, the
adopted design: 0/+5 V gate drive from I+, tap FETs' sources on the tap nodes, isolation-gate boot). Colours are the brand tokens (brand/tokens.yaml), embedded in each SVG.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))



INK, MUTED, RULE, SURFACE, ACCENT, PAPER = "#292b31", "#545866", "#d3d6df", "#eef0f4", "#23699f", "#ffffff"
CSS = f"""
.w {{ fill: none; stroke: {INK}; stroke-width: 1.5; stroke-linejoin: round; stroke-linecap: round; }}
.plate {{ stroke-width: 2.2; }}
.acc {{ stroke: {ACCENT}; stroke-width: 2.2; }}
.para {{ stroke-dasharray: 5 3; }}
.accf {{ fill: {ACCENT}; }}
.dot, .arrow {{ fill: {INK}; }}
.amp {{ fill: {PAPER}; stroke: {INK}; stroke-width: 1.6; }}
.pad {{ fill: {PAPER}; stroke: {INK}; stroke-width: 1.4; }}
.term {{ fill: {PAPER}; stroke: {INK}; stroke-width: 1.8; }}
.flag {{ fill: {SURFACE}; stroke: {INK}; stroke-width: 1.2; }}
.box {{ fill: {SURFACE}; stroke: {INK}; stroke-width: 1.6; }}
.grp {{ fill: {SURFACE}; stroke: none; }}
text {{ font-family: "JetBrains Mono", monospace; fill: {INK}; }}
.lbl, .ref {{ font-size: 12px; font-weight: 500; }}
.val {{ font-size: 11.5px; fill: {MUTED}; }}
.valsm {{ font-size: 10.5px; fill: {MUTED}; }}
.node {{ font-size: 12px; font-weight: 500; font-style: italic; }}
.net {{ font-size: 11px; font-weight: 500; }}
.pin {{ font-size: 13px; font-weight: 600; }}
.termlbl {{ font-size: 12.5px; font-weight: 600; }}
.accl {{ font-size: 12px; font-weight: 600; fill: {ACCENT}; }}
.grplbl {{ font-size: 10px; font-weight: 600; letter-spacing: .08em; fill: {MUTED}; }}
.note {{ font-family: "Inter", sans-serif; font-size: 12px; fill: {MUTED}; }}
"""


class S:
    def __init__(self):
        self.p = []

    def add(self, s):
        self.p.append(s)

    def wire(self, *pts, cls='w'):
        self.add(f'<polyline class="{cls}" points="{" ".join(f"{x},{y}" for x, y in pts)}"/>')

    def dot(self, x, y):
        self.add(f'<circle class="dot" cx="{x}" cy="{y}" r="3"/>')

    def text(self, x, y, s, a='middle', cls='lbl'):
        self.add(f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{a}">{s}</text>')

    def res(self, x1, y1, x2, y2, cls='w', body=36):
        """zigzag resistor between two pins (horizontal or vertical)"""
        if y1 == y2:
            L = x2 - x1; a = x1 + (L - body) / 2; b = a + body
            pts = [(x1, y1), (a, y1)]
            n = 6
            for i in range(n):
                pts.append((a + body * (i + 0.5) / n, y1 + (-6 if i % 2 == 0 else 6)))
            pts += [(b, y1), (x2, y2)]
        else:
            L = y2 - y1; a = y1 + (L - body) / 2; b = a + body
            pts = [(x1, y1), (x1, a)]
            n = 6
            for i in range(n):
                pts.append((x1 + (-6 if i % 2 == 0 else 6), a + body * (i + 0.5) / n))
            pts += [(x1, b), (x2, y2)]
        self.wire(*[(round(x, 1), round(y, 1)) for x, y in pts], cls=cls)

    def cap(self, x1, y1, x2, y2, cls='w'):
        if y1 == y2:
            m = (x1 + x2) / 2
            self.wire((x1, y1), (m - 4, y1), cls=cls); self.wire((m + 4, y1), (x2, y2), cls=cls)
            self.wire((m - 4, y1 - 11), (m - 4, y1 + 11), cls=cls + ' plate'); self.wire((m + 4, y1 - 11), (m + 4, y1 + 11), cls=cls + ' plate')
        else:
            m = (y1 + y2) / 2
            self.wire((x1, y1), (x1, m - 4), cls=cls); self.wire((x1, m + 4), (x2, y2), cls=cls)
            self.wire((x1 - 11, m - 4), (x1 + 11, m - 4), cls=cls + ' plate'); self.wire((x1 - 11, m + 4), (x1 + 11, m + 4), cls=cls + ' plate')

    def gnd(self, x, y):
        self.wire((x, y), (x, y + 8))
        for i, w in enumerate((10, 6, 2)):
            self.wire((x - w, y + 8 + 4 * i), (x + w, y + 8 + 4 * i))

    def opamp(self, cx, cy, top='-'):
        self.add(f'<polygon class="amp" points="{cx - 30},{cy - 32} {cx - 30},{cy + 32} {cx + 32},{cy}"/>')
        bot = '+' if top == '-' else '−'
        self.text(cx - 22, cy - 11, '−' if top == '-' else '+', 'middle', 'pin')
        self.text(cx - 22, cy + 19, bot, 'middle', 'pin')
        self.wire((cx - 30, cy - 15), (cx - 36, cy - 15)); self.wire((cx - 30, cy + 15), (cx - 36, cy + 15))
        self.wire((cx + 32, cy), (cx + 36, cy))

    def nmos(self, cx, cy, rot, mirror=False):
        """vertical-prototype NMOS (D top, S bottom, G left), rotated: -90 -> D left/S right/G bottom,
        90 -> S left/D right/G top; mirror flips it top-bottom after rotating (90 -> S left/D right/G bottom)"""
        g = ['<polyline class="w" points="0,-30 0,-15 -9,-15"/>',
             '<polyline class="w" points="0,30 0,15 -9,15"/>',
             '<polyline class="w" points="-9,0 0,0 0,15"/>',
             '<line class="w plate" x1="-9" y1="-21" x2="-9" y2="-9"/>',
             '<line class="w plate" x1="-9" y1="-5" x2="-9" y2="5"/>',
             '<line class="w plate" x1="-9" y1="9" x2="-9" y2="21"/>',
             '<line class="w plate" x1="-16" y1="-17" x2="-16" y2="17"/>',
             '<polyline class="w" points="-30,0 -16,0"/>',
             '<polygon class="arrow" points="-9,0 -3,-3.5 -3,3.5"/>']
        m = ' scale(1 -1)' if mirror else ''
        self.add(f'<g transform="translate({cx} {cy}){m} rotate({rot})">' + ''.join(g) + '</g>')

    def switch(self, x1, x2, y):
        self.wire((x1, y), (x1 + 14, y)); self.wire((x2 - 14, y), (x2, y))
        self.add(f'<circle class="pad" cx="{x1 + 16}" cy="{y}" r="2.5"/><circle class="pad" cx="{x2 - 16}" cy="{y}" r="2.5"/>')
        self.wire((x1 + 18, y - 1), (x2 - 16, y - 13))

    def flag(self, x, y, label, side='left'):
        """net label; wire attaches at (x, y). side = where the flag body sits"""
        w = 9 + 7.2 * len(label)
        if side == 'left':
            pts = [(x, y), (x - 8, y - 9), (x - 8 - w, y - 9), (x - 8 - w, y + 9), (x - 8, y + 9)]
            tx = x - 8 - w / 2
        else:
            pts = [(x, y), (x + 8, y - 9), (x + 8 + w, y - 9), (x + 8 + w, y + 9), (x + 8, y + 9)]
            tx = x + 8 + w / 2
        self.add(f'<polygon class="flag" points="{" ".join(f"{a:.0f},{b:.0f}" for a, b in pts)}"/>')
        self.text(tx, y + 4, label, 'middle', 'net')

    def term(self, x, y, label, a='start', dx=10):
        self.add(f'<circle class="term" cx="{x}" cy="{y}" r="5"/>')
        self.text(x + dx, y + 4, label, a, 'termlbl')

    def isrc(self, x, y1, y2, label=None, val=None):
        """current source between (x, y1) top and (x, y2) bottom; arrow points down (current y1 -> y2)"""
        m = (y1 + y2) / 2
        self.wire((x, y1), (x, m - 16)); self.wire((x, m + 16), (x, y2))
        self.add(f'<circle class="amp" cx="{x}" cy="{m}" r="16"/>')
        self.wire((x, m - 9), (x, m + 8))
        self.add(f'<polygon class="arrow" points="{x - 4},{m + 3} {x + 4},{m + 3} {x},{m + 10}"/>')
        if label:
            self.text(x + 24, m - 2, label, 'start', 'lbl')
        if val:
            self.text(x + 24, m + 13, val, 'start', 'valsm')

    def vsrc(self, x, y1, y2, label=None, val=None, plus_low=False):
        """voltage source between (x, y1) top and (x, y2) bottom; + on top unless plus_low"""
        m = (y1 + y2) / 2
        self.wire((x, y1), (x, m - 16)); self.wire((x, m + 16), (x, y2))
        self.add(f'<circle class="amp" cx="{x}" cy="{m}" r="16"/>')
        top, bot = ('−', '+') if plus_low else ('+', '−')
        self.text(x, m - 3, top, 'middle', 'pin'); self.text(x, m + 12, bot, 'middle', 'pin')
        if label:
            self.text(x + 24, m - 2, label, 'start', 'lbl')
        if val:
            self.text(x + 24, m + 13, val, 'start', 'valsm')

    def box(self, x, y, w, h, title, lines=(), cls='box'):
        self.add(f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="3"/>')
        self.text(x + w / 2, y + 18, title, 'middle', 'ref')
        for i, l in enumerate(lines):
            self.text(x + w / 2, y + 36 + 14 * i, l, 'middle', 'valsm')

    def svg(self, w, h, label):
        return (f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{label}" '
                f'xmlns="http://www.w3.org/2000/svg"><style>{CSS}</style>'
                f'<rect width="{w}" height="{h}" fill="{PAPER}"/>' + ''.join(self.p) + '</svg>')


# ---------------------------------------------------------------- figure 0: why the follower exists
def boot_why():
    """tap 6 with Qi off: Qi's own capacitances to I+ without the follower, bootstrapped with it"""
    s = S()

    def panel(ox, booted):
        x0, yi, yg, xq = ox + 70, 180, 100, ox + 250
        xd, xs, xr = xq - 55, xq + 55, xq + 200        # C_GD / C_DS taps on the drain and source wires; gm rail
        s.text(ox + 20, 30, 'With the follower' if booted else 'Without the follower', 'start', 'ref')
        s.term(x0, 45, 'I+', 'start', 12)
        s.wire((x0, 50), (x0, 65)); s.res(x0, 65, x0, 140, body=40); s.wire((x0, 140), (x0, yi))
        s.text(x0 - 14, 98, 'R_tap', 'end', 'ref'); s.text(x0 - 14, 112, '1 kΩ', 'end', 'val')
        s.text(x0 - 14, 126, '(tap 6)', 'end', 'valsm')
        s.dot(x0, yi); s.text(x0 - 10, yi + 4, 'I−', 'end', 'node')
        s.wire((x0, yi), (x0, 375)); s.term(x0, 380, 'to DUT', 'start', 12)
        # Qi, off: drain on I-, source on ihi, gate on top; its C_GD and C_DS drawn beside it (dashed)
        s.nmos(xq, yi, -90, mirror=True)
        s.wire((x0, yi), (xq - 30, yi)); s.dot(xd, yi)
        s.text(xq + 8, yi - 42, 'Qi (off)', 'start', 'ref'); s.text(xq + 8, yi - 29, 'CSD17577Q3A', 'start', 'valsm')
        s.text(xq - 30, yi + 15, 'D', 'middle', 'valsm'); s.text(xq + 30, yi + 15, 'S', 'middle', 'valsm')
        s.wire((xq, yi - 30), (xq, yg)); s.dot(xq, yg)
        s.cap(xd, yg, xd, yi, cls='w para'); s.wire((xd, yg), (xq, yg), cls='w para')
        s.text(xd - 16, (yg + yi) / 2 + 4, 'C_GD', 'end', 'ref')
        s.wire((xd, yi), (xd, yi + 60), cls='w para'); s.cap(xd, yi + 60, xs, yi + 60, cls='w para')
        s.wire((xs, yi + 60), (xs, yi), cls='w para')
        s.text(xq, yi + 88, 'C_DS', 'middle', 'ref')
        s.wire((xq + 30, yi), (xq + 90, yi)); s.dot(xs, yi)
        s.text(xq + 76, yi - 8, 'ihi', 'middle', 'node')
        s.text(xq - 8, yg - 8, 'Qi gate', 'end', 'node')
        if not booted:
            xg = xq + 120
            s.wire((xq, yg), (xg, yg)); s.wire((xg, yg), (xg, yg + 18)); s.gnd(xg, yg + 18)
            s.text(xg + 12, yg + 4, 'driver low: I+', 'start', 'valsm')
            s.wire((xq + 90, yi), (xg, yi)); s.res(xg, yi, xg, yi + 70, body=30); s.gnd(xg, yi + 70)
            s.text(xg + 12, yi + 34, 'Rtih 1 kΩ', 'start', 'ref'); s.text(xg + 12, yi + 48, 'to I+', 'start', 'valsm')
            s.wire((x0 + 15, yi - 12), (xd - 18, yi - 12), cls='w acc')
            s.add(f'<polygon class="accf" points="{xd - 12},{yi - 12} {xd - 20},{yi - 16} {xd - 20},{yi - 8}"/>')
            s.text((x0 + xd) / 2, yi - 20, 'i = C·dV/dt', 'middle', 'accl')
            notes = ['Off, Qi still has ~0.8 nF from I− to nodes held at I+.',
                     'The DUT current charges it: a pole at the node,',
                     '204 kHz simulated; 236 kHz at the ADC, below 310 kHz.']
        else:
            xb, cx, cy = xq + 110, ox + 250, 335
            # Qb: ties Qi's gate to gm while Qi is off
            s.nmos(xb, yg, -90)
            s.wire((xq, yg), (xb - 30, yg)); s.wire((xb + 30, yg), (xr, yg), cls='w acc')
            s.text(xb, yg - 22, 'Qb (on)', 'middle', 'accl'); s.text(xb, yg + 44, 'EN_B', 'middle', 'valsm')
            s.res(xq + 90, yi, xr, yi, cls='w acc', body=30); s.dot(xr, yi)
            s.text((xq + 90 + xr) / 2, yi + 22, 'Rtih 1 kΩ', 'middle', 'accl')
            s.wire((xr, yg), (xr, cy)); s.dot(xr, cy)
            s.opamp(cx, cy)
            s.wire((x0, cy + 15), (cx - 36, cy + 15)); s.dot(x0, cy + 15)
            s.wire((cx + 36, cy), (xr, cy)); s.dot(cx + 52, cy)
            s.wire((cx + 52, cy), (cx + 52, cy - 44), (cx - 46, cy - 44), (cx - 46, cy - 15), (cx - 36, cy - 15))
            s.text(xr + 8, cy + 4, 'gm', 'start', 'node')
            s.text(cx + 4, cy + 52, 'follower U7 (OPA2156)', 'middle', 'ref')
            s.text((x0 + xd) / 2, yi - 20, 'V across C ≈ 0', 'middle', 'accl')
            notes = ['The follower copies V(I−) onto Qi\'s gate (through Qb)',
                     'and onto ihi (through Rtih): no voltage across C_GD or',
                     'C_DS. Simulated: 553 kHz at the ADC, +0.6 dB.']
        for i, l in enumerate(notes):
            s.text(ox + 20, 420 + 16 * i, l, 'start', 'note')
    panel(0, False)
    s.add('<line class="w" x1="550" y1="20" x2="550" y2="460" stroke-dasharray="2 4"/>')
    panel(560, True)
    return s.svg(1120, 480, 'Tap 6 with the isolation FET Qi off. Left: its gate-drain and drain-source capacitance, about 0.8 nF, '
                            'go from I minus to nodes held at I+, which slows tap 6 to 236 kHz at the ADC. Right: Qb and Rtih '
                            'tie the gate and ihi to a follower that copies the voltage of I minus, so no current flows through them.')


# ---------------------------------------------------------------- figure 1: ladder, switches, drivers, follower, stage 1
def driver(s, x, y, en, rail, acc=False, top=False):
    """UCC27524 channel: buffer triangle (input left, output right at x + 26), EN label, low-rail label"""
    c = ' acc' if acc else ''
    s.add(f'<polygon class="amp{c}" points="{x},{y - 11} {x},{y + 11} {x + 22},{y}"/>')
    s.wire((x - 10, y), (x, y)); s.wire((x + 22, y), (x + 26, y))
    if top:
        s.text(x + 8, y - 16, en, 'middle', 'valsm')
    else:
        s.text(x - 13, y + 4, en, 'end', 'valsm')
    s.text(x + 8, y + 24, rail, 'middle', 'accl' if acc else 'valsm')


def front_end():
    """6-range ladder (RANGES=6, G6=boot in gen_decks.py)"""
    s = S()
    XL, FC, BUS, ISO, IM = 300, 480, 560, 660, 1040
    FD, FS_ = FC - 30, FC + 30
    Y = {0: 90}
    for k in range(1, 7):
        Y[k] = 90 + 110 * k
    rseg = ['10 mΩ', '90 mΩ', '900 mΩ', '9 Ω', '90 Ω', '900 Ω']
    cum = ['10 mΩ', '100 mΩ', '1 Ω', '10 Ω', '100 Ω', '1 kΩ']
    fs = ['2 A', '200 mA', '20 mA', '2 mA', '200 µA', '20 µA']
    part = [('Q1A ‖ Q1B', '2× CSD17577Q3A'), ('Q2', 'AO3400A'), ('Q3', 'AO3400A'),
            ('Q4', '2N7002E'), ('Q5', '2N7002E'), ('Q6', '2N7002E')]
    for y0, y1, name in ((146, 492, 'GROUP H'), (497, 822, 'GROUP M')):
        s.add(f'<rect class="grp" x="392" y="{y0}" width="132" height="{y1 - y0}" rx="4"/>')
        s.text(396, y0 + 12, name, 'start', 'grplbl')
    s.wire((XL, 52), (XL, Y[0]))
    s.term(XL, 47, 'I+ · island GND (DUT supply side)', 'start', 12)
    s.dot(XL, Y[0])
    s.wire((XL, Y[0]), (XL - 40, Y[0])); s.gnd(XL - 40, Y[0])
    for k in range(1, 7):
        s.res(XL, Y[k - 1], XL, Y[k], body=40)
        s.text(XL - 14, (Y[k - 1] + Y[k]) / 2 - 2, f'R{k}', 'end', 'ref')
        s.text(XL - 14, (Y[k - 1] + Y[k]) / 2 + 12, rseg[k - 1], 'end', 'val')
        s.dot(XL, Y[k])
        s.text(XL + 8, Y[k] - 7, f't{k}', 'start', 'node')
        s.text(XL + 8, Y[k] + 15, cum[k - 1], 'start', 'valsm')
        s.text(XL + 8, Y[k] + 28, fs[k - 1], 'start', 'valsm')
    for k, net in ((3, 'SENSE_A'), (5, 'SENSE_B'), (6, 'SENSE_C')):
        s.wire((XL, Y[k]), (XL - 62, Y[k]))
        s.flag(XL - 62, Y[k], net, 'left')
    # tap switches: UCC27524 (GND on I+) -> 22 ohm -> gate; source on the tap node
    for k in range(1, 7):
        y = Y[k]
        s.wire((XL, y), (FD, y))
        s.nmos(FC, y, 90, mirror=True)
        if k in (1, 4):
            s.text(FD - 2, y + 14, 'S', 'end', 'valsm'); s.text(FS_ + 2, y + 14, 'D', 'start', 'valsm')
        s.wire((FS_, y), (BUS if k <= 3 else IM, y))
        if k > 3:
            s.dot(IM, y)
        s.text(FC, y - 24, part[k - 1][0], 'middle', 'ref')
        s.text(FC, y - 11, part[k - 1][1], 'middle', 'valsm')
        yd = y + 52
        driver(s, 398, yd, f'EN{k}', 'GND = I+')
        s.res(424, yd, FC, yd, body=22)
        s.wire((FC, yd), (FC, y + 30))
        s.text(452, yd - 9, '22 Ω', 'middle', 'valsm')
    # group H bus and its isolation FET
    IHI_END = 500
    s.wire((BUS, Y[1]), (BUS, IHI_END)); s.text(BUS + 6, Y[1] - 8, 'ihi', 'start', 'node')
    for k in range(1, 4):
        s.dot(BUS, Y[k])
    y = Y[2]
    s.nmos(ISO, y, 90)
    s.wire((BUS, y), (ISO - 30, y)); s.wire((ISO + 30, y), (IM, y)); s.dot(IM, y)
    s.text(ISO, y + 24, 'Qi', 'middle', 'ref'); s.text(ISO, y + 38, 'CSD17577Q3A', 'middle', 'valsm')
    yd = y - 70
    driver(s, 590, yd, 'EN_ISO', 'GND = I+', top=True)
    s.res(616, yd, ISO, yd, body=20); s.wire((ISO, yd), (ISO, y - 30)); s.dot(ISO, yd)
    s.text(640, yd - 9, '330 Ω', 'middle', 'accl')
    s.wire((ISO, yd), (ISO + 40, yd), cls='w acc')
    s.nmos(ISO + 70, yd, -90)
    s.flag(ISO + 100, yd, 'gm', 'right')
    s.text(ISO + 70, yd - 24, 'Qb', 'middle', 'accl'); s.text(ISO + 70, yd - 11, '2N7002E', 'middle', 'valsm')
    s.text(ISO + 78, yd + 44, 'EN_B = ¬EN_ISO', 'start', 'valsm')
    # I- bus and terminal
    s.wire((IM, Y[2]), (IM, 830))
    s.term(IM, 835, 'I− · to DUT', 'start', 12)
    s.text(IM + 6, Y[2] - 8, 'I−', 'start', 'node')
    # the follower: boots Qi's gate (Qb) and holds ihi (Rtih)
    cx, cy, OUT = 850, 420, 930
    s.opamp(cx, cy)
    s.flag(cx - 56, cy + 15, 'I−', 'left'); s.wire((cx - 56, cy + 15), (cx - 36, cy + 15))
    s.wire((cx + 36, cy), (OUT, cy)); s.dot(cx + 52, cy)
    s.wire((cx + 52, cy), (cx + 52, cy - 46), (cx - 46, cy - 46), (cx - 46, cy - 15), (cx - 36, cy - 15))
    s.text(cx + 8, cy - 54, 'U7 · OPA2156 · follower on I−', 'middle', 'ref')
    s.flag(OUT, cy, 'gm', 'right')
    s.text(OUT + 6, cy + 24, 'to Qb and Rtih', 'start', 'valsm')
    # Rtih: ihi to gm, drawn to a flag so it doesn't run past the follower's input
    QX = 600
    s.wire((BUS, IHI_END), (QX, IHI_END))
    s.res(QX, IHI_END, QX + 110, IHI_END, cls='w acc', body=26)
    s.flag(QX + 110, IHI_END, 'gm', 'right')
    s.text(QX + 55, IHI_END + 18, 'Rtih 1 kΩ', 'middle', 'accl')
    # stage 1, one per chain, all OPA210
    def stage1(cy, net, ref, prt, rg, rf, gain, rails):
        cx = 1300
        s.flag(1190, cy - 15, net, 'left'); s.wire((1190, cy - 15), (cx - 36, cy - 15))
        s.opamp(cx, cy, top='+')
        n = (cx - 45, cy + 15)
        s.wire((cx - 36, cy + 15), n); s.dot(*n)
        s.wire(n, (cx - 45, cy + 55)); s.dot(cx - 45, cy + 55)
        s.res(cx - 45, cy + 55, cx + 45, cy + 55, body=30)
        s.wire((cx + 45, cy + 55), (cx + 45, cy)); s.wire((cx + 36, cy), (cx + 70, cy)); s.dot(cx + 45, cy)
        s.res(cx - 45, cy + 55, cx - 45, cy + 105, body=26); s.gnd(cx - 45, cy + 105)
        s.text(cx, cy + 75, rf, 'middle', 'val'); s.text(cx - 54, cy + 84, rg, 'end', 'val')
        s.text(cx, cy - 62, ref, 'middle', 'ref'); s.text(cx, cy - 47, f'{prt} · {gain} · {rails}', 'middle', 'valsm')
        s.flag(cx + 70, cy, 'STAGE2', 'right')
    stage1(230, 'SENSE_A', 'Chain A stage 1 · taps 1–3', 'OPA210', '64 Ω', '255 Ω', '×4.98', '±5 V')
    stage1(480, 'SENSE_B', 'Chain B stage 1 · taps 4–5', 'OPA210', '64 Ω', '255 Ω', '×4.98', '±5 V')
    stage1(730, 'SENSE_C', 'Chain C stage 1 · tap 6', 'OPA387', '105 Ω', '324 Ω', '×4.09', '±2.5 V')
    s.text(1300, 885, 'STAGE2 → stage 2, stage 3, AAF, ADC (chain figure)', 'middle', 'note')
    s.wire((40, 905), (70, 905), cls='w acc')
    s.text(78, 909, 'Isolation-gate boot: every driver 0 / +5 V from I+; while Qi is off, Qb ties its gate to the follower, '
           'which also holds ihi through Rtih', 'start', 'note')
    return s.svg(1470, 925, 'Front end as simulated: a 6-tap shunt ladder from I+ to I minus; each tap switch with its UCC27524 '
                            'driver referenced to I+ and 22 ohm gate resistor; group H behind the isolation FET Qi, whose gate '
                            'is tied to the follower U7 by Qb while off; group M straight on I minus; and the stage-1 amplifiers '
                            'on sense taps 3, 5 and 6 (OPA210, OPA210, OPA387).')


# ---------------------------------------------------------------- figure 2: one AFE2 -> AAF -> ADC chain
def chain():
    s = S()
    cy = 120

    def noninv(cx, name, prt, rg, rf, gain):
        s.opamp(cx, cy, top='+')
        n = (cx - 45, cy + 15)
        s.wire((cx - 36, cy + 15), n); s.dot(*n)
        s.wire(n, (cx - 45, cy + 55)); s.dot(cx - 45, cy + 55)
        s.res(cx - 45, cy + 55, cx + 45, cy + 55, body=34)
        s.wire((cx + 45, cy + 55), (cx + 45, cy)); s.wire((cx + 36, cy), (cx + 45, cy)); s.dot(cx + 45, cy)
        s.res(cx - 45, cy + 55, cx - 45, cy + 105, body=30); s.gnd(cx - 45, cy + 105)
        s.text(cx, cy + 75, rf, 'middle', 'val'); s.text(cx - 54, cy + 84, rg, 'end', 'val')
        s.text(cx, cy - 46, name, 'middle', 'ref'); s.text(cx, cy - 32, f'{prt} · {gain}', 'middle', 'valsm')

    s.flag(70, cy - 15, 'SENSE_x', 'left')
    s.wire((70, cy - 15), (164, cy - 15))
    noninv(200, 'Stage 1 (AFE1)', 'OPA210 / OPA387', 'Rg', 'Rf', 'see table')
    s.wire((245, cy), (290, cy), (290, cy - 15), (384, cy - 15))
    noninv(420, 'Stage 2', 'OPA2189', 'Rg_s2', 'Rf_s2', '×5.00 / ×6.12')
    # stage 3, inverting -4.51
    cx = 680
    s.wire((465, cy), (520, cy), (520, cy - 15), (545, cy - 15))
    s.res(545, cy - 15, cx - 45, cy - 15, body=34); s.dot(cx - 45, cy - 15)
    s.text((545 + cx - 45) / 2, cy - 1, '255 Ω', 'middle', 'val')
    s.opamp(cx, cy, top='-')
    s.wire((cx - 45, cy - 15), (cx - 36, cy - 15))
    s.wire((cx - 45, cy - 15), (cx - 45, cy - 60)); s.res(cx - 45, cy - 60, cx + 45, cy - 60, body=34)
    s.wire((cx + 45, cy - 60), (cx + 45, cy)); s.wire((cx + 36, cy), (cx + 45, cy)); s.dot(cx + 45, cy)
    s.text(cx, cy - 72, '1.15 kΩ', 'middle', 'val')
    s.wire((cx - 36, cy + 15), (cx - 40, cy + 15), (cx - 40, cy + 30)); s.gnd(cx - 40, cy + 30)
    s.text(cx + 30, cy + 66, 'Stage 3 · OPA2189 · −4.51', 'middle', 'ref')
    s.wire((cx + 45, cy), (820, cy)); s.flag(820, cy, 'AAF_IN', 'right')

    # AAF row
    cy = 470
    s.flag(70, cy - 15, 'AAF_IN', 'left')
    # the adopted filter (TR-0002 tbl-aaf: transitional m = 0.8, 650 kHz; the board had the 719 kHz Butterworth)
    vals = [('30.1k', '6.81k', '30.1k', '24p', '10p'), ('26.1k', '5.76k', '26.1k', '33p', '10p'),
            ('17.8k', '3.92k', '17.8k', '68p', '10p'), ('6.65k', '1.74k', '6.65k', '390p', '10p')]
    prev = (70, cy - 15)
    for i, (r1, r2, r3, c1, c2) in enumerate(vals):
        cx = 260 + 228 * i
        x1 = cx - 160
        s.wire(prev, (x1, cy - 15)) if prev[1] == cy - 15 else s.wire(prev, (x1, cy), (x1, cy - 15))
        n1 = (cx - 100, cy - 15); n2 = (cx - 45, cy - 15)
        s.res(x1, cy - 15, *n1, body=30); s.dot(*n1)
        s.res(*n1, *n2, body=28); s.dot(*n2)
        s.wire(n2, (cx - 36, cy - 15))
        s.cap(n1[0], n1[1], n1[0], cy + 35); s.gnd(n1[0], cy + 35)
        s.wire(n2, (cx - 45, cy - 55)); s.cap(cx - 45, cy - 55, cx + 45, cy - 55)
        s.wire((cx + 45, cy - 55), (cx + 58, cy - 55)); s.dot(cx + 58, cy - 55)   # C2 joins the output node's riser
        s.wire(n1, (n1[0], cy - 95)); s.res(n1[0], cy - 95, cx + 58, cy - 95, body=36)
        s.wire((cx + 58, cy - 95), (cx + 58, cy))
        s.opamp(cx, cy, top='-')
        s.wire((cx + 36, cy), (cx + 58, cy)); s.dot(cx + 58, cy)
        s.wire((cx - 36, cy + 15), (cx - 40, cy + 15), (cx - 40, cy + 30)); s.gnd(cx - 40, cy + 30)
        s.text((x1 + n1[0]) / 2, cy - 25, r1, 'middle', 'val')
        s.text((n1[0] + n2[0]) / 2, cy - 25, r2, 'middle', 'val')
        s.text(n1[0] + 16, cy + 18, c1, 'start', 'val')
        s.text(cx, cy - 70, c2, 'middle', 'val')
        s.text((n1[0] + cx + 58) / 2, cy - 105, r3, 'middle', 'val')
        s.text(cx + 4, cy + 64, f'Biquad {i + 1}', 'middle', 'ref')
        prev = (cx + 58, cy)
    s.text(480, cy - 140, 'Anti-alias filter: 8th-order transitional (m = 0.8, 650 kHz), 4× MFB biquad, OPA4189', 'middle', 'ref')
    # ADC input network + ADC
    xo = prev[0]
    s.wire(prev, (xo + 12, cy))
    s.res(xo + 12, cy, xo + 70, cy, body=30); s.text(xo + 41, cy - 12, '5 Ω', 'middle', 'val')
    a = xo + 82
    s.wire((xo + 70, cy), (a + 40, cy)); s.dot(a, cy)
    s.cap(a, cy, a, cy + 60, cls='w acc'); s.dot(a, cy + 60)
    s.text(a - 16, cy + 34, '47 pF', 'end', 'accl')
    s.wire((a, cy + 60), (a + 40, cy + 60))
    s.res(a, cy + 60, a, cy + 115, body=30); s.gnd(a, cy + 115); s.text(a - 12, cy + 92, '5 Ω', 'end', 'val')
    bx = a + 40
    s.add(f'<rect class="box" x="{bx}" y="{cy - 40}" width="96" height="130" rx="3"/>')
    s.text(bx + 6, cy + 4, 'AIN0', 'start', 'valsm'); s.text(bx + 6, cy + 64, 'AIN0GND', 'start', 'valsm')
    s.text(bx + 48, cy - 20, 'RS1473', 'middle', 'ref'); s.text(bx + 48, cy + 30, '14-bit', 'middle', 'valsm')
    s.text(bx + 48, cy + 44, '2 MSPS', 'middle', 'valsm')
    s.text(a - 16, cy + 48, 'board: 470 pF', 'end', 'valsm')
    return s.svg(bx + 110, 600, 'One measurement chain: stage 1 at the sense tap, stage 2 non-inverting gain, stage 3 '
                                 'inverting gain of minus 4.51, four multiple-feedback biquads, and the ADC input network.')


# ---------------------------------------------------------------- figure 3: guard-resistor mechanism (rejected arrangement)
def mechanism():
    s = S()
    y = 100
    s.wire((60, y), (300, y)); s.text(66, y - 10, 'I−', 'start', 'node')
    s.add('<polygon class="arrow" points="60,96 60,104 70,100"/>')
    s.text(40, y + 4, 'I_DUT', 'end', 'valsm')
    s.dot(110, y); s.res(110, y, 110, 200, body=40); s.gnd(110, 200)
    s.text(124, 146, 'R_tap', 'start', 'ref'); s.text(124, 160, '10 kΩ / 100 kΩ', 'start', 'valsm')
    s.dot(190, y); s.wire((190, y), (190, 280), (284, 280))
    s.opamp(320, 265, top='-')
    s.text(320, 320, 'guard (OPA2156), not fitted', 'middle', 'ref')
    s.wire((356, 265), (380, 265)); s.dot(380, 265)
    s.wire((380, 265), (380, 215), (270, 215), (270, 250), (284, 250))
    s.cap(300, y, 440, y)
    s.text(370, y - 22, 'C', 'middle', 'ref'); s.text(370, y + 28, 'Qi / Qi2 C_oss', 'middle', 'valsm')
    s.dot(520, y); s.wire((440, y), (640, y)); s.text(526, y - 10, 'ihi / ilo', 'start', 'node')
    s.wire((380, 265), (520, 265))
    s.res(520, 265, 520, y, cls='w acc', body=44)
    s.text(534, 178, 'R_s', 'start', 'accl'); s.text(534, 192, 'Rgo + Qg R_on', 'start', 'valsm')
    s.cap(640, y, 640, 200); s.gnd(640, 200)
    s.text(656, 146, 'C_g ≈ 9.6 nF', 'start', 'ref'); s.text(656, 160, 'mostly off tap-FET C_GS', 'start', 'valsm')
    s.text(656, 174, 'to their driver rails', 'start', 'valsm')
    return s.svg(780, 340, 'Equivalent circuit of the rejected low-resistance guard: the guard follower drives the isolated node through R_s into C_g, '
                           'so the node lags I minus and current flows through the coupling capacitance C.')



# ---------------------------------------------------------------- figure 4: EN_ISO / EN_B from EN1-EN3
def enable_logic():
    """EN_ISO and EN_B derived on the island from EN1-EN3: diode-OR, asymmetric RC, UCC27525 inputs"""
    s = S()

    def diode(x, y):
        s.add(f'<polygon class="amp" points="{x},{y - 7} {x},{y + 7} {x + 13},{y}"/>')
        s.wire((x + 13, y - 7), (x + 13, y + 7), cls='w plate')

    def block(y0, rs, rsh, cap, title, out, gate, rg, inv, notes):
        ys = [y0 + 20, y0 + 50, y0 + 80]
        s.text(40, y0 - 8, title, 'start', 'accl')
        for k, y in enumerate(ys, 1):
            s.flag(110, y, f'EN{k}', 'left')
            s.wire((110, y), (140, y)); diode(140, y); s.wire((153, y), (180, y))
        s.wire((180, ys[0]), (180, ys[2])); s.dot(180, ys[1])
        ym = ys[1]
        s.res(180, ym, 300, ym, body=36)
        s.text(240, ym - 14, rs, 'middle', 'val')
        s.wire((300, ym), (500, ym))
        s.text(346, ym - 10, 'A' if not inv else 'B', 'start', 'node')
        s.res(340, ym, 340, ym + 90, body=36); s.gnd(340, ym + 90); s.dot(340, ym)
        s.text(352, ym + 50, rsh, 'start', 'val')
        s.cap(450, ym, 450, ym + 90); s.gnd(450, ym + 90); s.dot(450, ym)
        s.text(468, ym + 50, f'{cap} C0G', 'start', 'val')
        x = 520
        s.wire((500, ym), (x, ym))
        s.add(f'<polygon class="amp" points="{x},{ym - 16} {x},{ym + 16} {x + 32},{ym}"/>')
        xo = x + 32
        if inv:
            s.add(f'<circle class="pad" cx="{xo + 4}" cy="{ym}" r="4"/>'); xo += 8
        s.text(x + 14, ym - 30, 'UCC27525 ' + ('inverting' if inv else 'non-inverting'), 'middle', 'valsm')
        s.text(x + 14, ym + 32, 'GND = I+, VDD +5 V', 'middle', 'valsm')
        s.res(xo, ym, xo + 90, ym, body=30)
        s.text(xo + 45, ym - 14, rg, 'middle', 'val')
        s.flag(xo + 90, ym, gate, 'right')
        s.text(xo + 60, ym + 32, out, 'start', 'accl')
        for i, n in enumerate(notes):
            s.text(900, ys[0] + 4 + 18 * i, n, 'start', 'note')

    block(40, '680 Ω', '6.8 kΩ', '100 pF', 'EN_ISO: Qi on ~0.14 µs after any of EN1–3, off ~0.55 µs after all low',
          'EN_ISO', 'Qi gate', '330 Ω', False,
          ['rise: A charges via 680 Ω ‖ 6.8 kΩ', '  τ ≈ 62 ns → ~0.14 µs to 2.1 V',
           'fall: A discharges via 6.8 kΩ', '  τ = 0.68 µs → ~0.55 µs to 1.2 V'])
    block(250, '100 Ω', '15 kΩ', '270 pF', 'EN_B: Qb off ~50 ns after any of EN1–3, on ~3.5 µs after all low',
          'EN_B', 'Qb gate', '22 Ω', True,
          ['rise: B charges via 100 Ω', '  τ = 27 ns → Qb off before Qi on',
           'fall: B discharges via 15 kΩ', '  τ = 4.05 µs → ~3.5 µs to 1.2 V,', '  ~3.0 µs after Qi off (≥ 1.56 µs',
           '  over all corners)'])
    s.text(40, 466, 'EN1–EN3 are the tap enables already on the island (3.3 V logic, referenced to I+). Diodes: Schottky (BAT54-class).',
           'start', 'note')
    s.text(40, 484, 'Thresholds: UCC27525 inputs, VIN_H 2.1 V / VIN_L 1.2 V typical (1.9–2.3 / 1.0–1.4 V limits). Timing holds at every limit; simulated in every deck.',
           'start', 'note')
    return s.svg(1180, 500, 'EN_ISO and EN_B derived on the island from EN1 to EN3: a diode-OR of the three enables '
                            'charges an RC node through a small resistor and discharges it through a large one, and '
                            'the UCC27525 input thresholds turn each node into a delayed edge: EN_ISO through the '
                            'non-inverting channel to Qi, EN_B through the inverting channel to Qb.')


# ---------------------------------------------------------------- WU-0007: test benches
def bench():
    """the ladder test bench every 6-range suite shares (gen_decks.ladder + stage1): I+ is node 0, the DUT is
    an ideal current source pulling the DUT current out of I-; probes on the ladder head, I- and the ADC nodes"""
    s = S()
    # I+ = ground, ladder head
    s.gnd(60, 300)
    s.text(60, 336, 'I+ = node 0', 'middle', 'node')
    s.wire((60, 300), (60, 120), (110, 120))
    s.res(110, 120, 190, 120, body=30); s.text(150, 104, 'Rhd 1 µΩ', 'middle', 'val')
    s.dot(200, 120); s.text(200, 104, 'hd', 'middle', 'node')
    s.wire((190, 120), (230, 120))
    s.box(230, 70, 170, 110, 'Ladder R1–R6', ['10 mΩ … 1 kΩ cumulative', 'nodes t1 … t6'])
    s.wire((400, 120), (450, 120))
    s.box(450, 60, 200, 130, 'Tap switches', ['2× CSD17577Q3A, AO3400A ×2,', '2N7002E ×3; UCC2752x drivers,', '22 Ω gates, GND on I+', 'EN1–EN6: PWL timeline'])
    s.box(450, 220, 200, 110, 'Isolation (group H)', ['Qi CSD17577Q3A, 330 Ω', 'Qb 2N7002E, U7 OPA2156', 'Rtih 330 Ω; ihi, gm'])
    s.box(220, 220, 180, 110, 'Enable network', ['BAT54 OR, RC nodes A, B', 'UCC27525 model', '→ EN_ISO, EN_B'])
    s.wire((400, 275), (450, 275))
    s.wire((550, 190), (550, 220))
    # I- and the DUT
    s.wire((650, 125), (730, 125)); s.wire((650, 275), (730, 275))
    s.wire((730, 125), (730, 400)); s.dot(730, 275)
    s.text(742, 140, 'I− (im)', 'start', 'node')
    s.isrc(730, 400, 500, 'Idut', 'PWL per suite')
    s.wire((730, 500), (730, 520)); s.gnd(730, 520)
    # chains
    for i, (c, node, part) in enumerate((('A', 't3', 'OPA210 ×4.98'), ('B', 't5', 'OPA210 ×4.98'), ('C', 't6', '2× OPA387 ×4.09, avg'))):
        y = 400 + 60 * i
        s.flag(90, y, node, 'left')
        s.wire((90, y), (130, y))
        s.box(130, y - 22, 150, 44, f'Stage 1 {c}', [part])
        s.wire((280, y), (310, y))
        s.box(310, y - 22, 190, 44, 'DOWNSTREAM', ['stage 2, 3, AAF, ADC net'])
        s.wire((500, y), (540, y)); s.dot(540, y); s.text(548, y + 4, f'ain{c}', 'start', 'node')
    s.text(130, 366, 'TI vendor models (noisy=0)', 'start', 'valsm')
    s.text(310, 366, 'behavioural (downstream_m080.inc)', 'start', 'valsm')
    s.text(60, 40, 'Probes: I(ladder) = V(hd) / 1 µΩ;  burden = −V(im);  reading = V(ainA … ainC)', 'start', 'note')
    s.text(60, 58, 'Rails ±5 V (stage 1 A/B), ±2.5 V (stage 1 C, U7), +5 V (drivers, from I+); every source ideal', 'start', 'note')
    return s.svg(880, 600, 'Ladder test bench: I+ is the simulator ground; the ladder, tap switches, isolation network and enable '
                           'network sit between it and I minus; an ideal current source draws the DUT current from I minus; three '
                           'stage-1 amplifiers and their downstream blocks give the ADC nodes')


def dut_bench():
    """DUT walks (characterize.walk): a 3.3 V supply returning through the ladder, a switched load conductance and
    decoupling between I- and the supply's return"""
    s = S()
    s.wire((80, 400), (80, 90), (140, 90))
    s.gnd(80, 400); s.text(80, 436, 'I+ = node 0', 'middle', 'node')
    s.box(140, 60, 170, 60, 'Ladder, switches', ['as the ladder bench'])
    s.wire((310, 90), (420, 90)); s.text(330, 80, 'I− (im)', 'start', 'node')
    s.wire((420, 90), (420, 130)); s.dot(420, 90)
    s.wire((420, 90), (560, 90), (560, 130))
    # load conductance
    s.add('<rect class="pad" x="404" y="150" width="32" height="60" rx="2"/>')
    s.wire((420, 130), (420, 150)); s.wire((420, 210), (420, 250))
    s.text(394, 172, 'Bload', 'end', 'lbl'); s.text(394, 188, 'I = V(im,dsup) × G(t)', 'end', 'valsm')
    s.text(394, 202, 'G: 1 µA → 50 mA at 3.3 V', 'end', 'valsm')
    # decoupling
    s.cap(560, 130, 560, 190); s.text(578, 164, 'Cdut 10 µF (1 µF, 100 nF)', 'start', 'val')
    s.res(560, 190, 560, 250, body=30); s.text(578, 224, 'ESR 10 mΩ', 'start', 'val')
    s.wire((420, 250), (560, 250)); s.dot(490, 250)
    s.wire((490, 250), (490, 280)); s.text(500, 272, 'dsup', 'start', 'node')
    s.vsrc(490, 280, 380, 'Vsup 3.3 V', 'dsup at −3.3 V against I+', plus_low=True)
    s.wire((490, 380), (490, 400), (80, 400))
    s.text(80, 30, 'DUT voltage = V(im) − V(dsup); DUT current = i(Vsup) (load + capacitor); Cdut starts charged (ic = 3.3 V)', 'start', 'note')
    return s.svg(900, 470, 'DUT test bench: a 3.3 volt supply returns through the ladder; the DUT is a switched load conductance '
                           'with its decoupling capacitor and ESR between I minus and the supply return')


def noise_bench():
    """where the transient-noise sources go (characterize.noise): every one a unit TRNOISE through a B-source gated by ngate"""
    s = S()
    # ladder segment with a parallel noise current
    s.wire((40, 120), (90, 120)); s.res(90, 120, 170, 120, body=30); s.wire((170, 120), (210, 120))
    s.text(130, 104, 'R_k', 'middle', 'val')
    s.wire((100, 120), (100, 160)); s.wire((160, 120), (160, 160))
    s.wire((100, 160), (114, 160)); s.wire((146, 160), (160, 160))
    s.add('<circle class="amp" cx="130" cy="160" r="16"/>')
    s.add('<polygon class="arrow" points="124,156 124,164 135,160"/>'); s.wire((120, 160), (130, 160))
    s.text(130, 200, '√(4kT/R_k) per √Hz', 'middle', 'valsm')
    s.text(130, 60, 'Every ladder segment', 'middle', 'ref')
    # stage-1 e_n in series with + input
    cx = 420
    s.opamp(cx, 140, top='+')
    s.wire((cx - 36, 125), (cx - 60, 125))
    s.add(f'<circle class="amp" cx="{cx - 76}" cy="125" r="16"/>'); s.text(cx - 76, 129, 'eₙ', 'middle', 'lbl')
    s.wire((cx - 92, 125), (cx - 130, 125)); s.flag(cx - 130, 125, 'tap node', 'left')
    s.text(cx - 10, 60, 'Stage 1 of the owner chain', 'middle', 'ref')
    s.text(cx - 10, 210, '√(eₙ² + 4kT·Rg‖Rf): OPA210 2.26, OPA387 8.5 nV/√Hz (chain C: one per half)', 'middle', 'valsm')
    # follower
    cx2 = 720
    s.opamp(cx2, 140, top='+')
    s.wire((cx2 - 36, 125), (cx2 - 60, 125))
    s.add(f'<circle class="amp" cx="{cx2 - 76}" cy="125" r="16"/>'); s.text(cx2 - 76, 129, 'eₙ', 'middle', 'lbl')
    s.wire((cx2 - 92, 125), (cx2 - 120, 125)); s.flag(cx2 - 120, 125, 'I−', 'left')
    s.text(cx2, 60, 'Follower U7', 'middle', 'ref'); s.text(cx2, 210, 'OPA2156 2.8 nV/√Hz', 'middle', 'valsm')
    s.text(40, 262, 'NOISE_DS=1 adds, in the owner chain\'s DOWNSTREAM block: 5.2 nV/√Hz on each OPA2189 / OPA4189 + input, and', 'start', 'note')
    s.text(40, 280, '√(4kT/R) across every resistor of stages 2–3, the filter and the ADC network. ADC noise is added in the analysis.', 'start', 'note')
    s.text(40, 304, 'Each source: Vnz (TRNOISE, unit density, Ts = 9.7 ns) → B-source × V(ngate); ngate steps 0 → 1 at 30–31 µs.', 'start', 'note')
    return s.svg(900, 320, 'Where the transient noise sources sit: a current source across every ladder resistor, a voltage '
                           'source in series with the owner chain stage-1 input and with the follower input, and with NOISE_DS the '
                           'downstream op-amps and resistors')


def aaf_bench():
    """aaf_sweep.py's standalone chain"""
    s = S()
    s.gnd(60, 200)
    s.vsrc(60, 100, 200, 'Vin', 'AC 1, or a PWL step')
    s.wire((60, 100), (60, 80), (130, 80))
    s.res(130, 80, 210, 80, body=30); s.text(170, 64, '1 kΩ', 'middle', 'val')
    s.wire((210, 80), (250, 80)); s.dot(230, 80)
    s.cap(230, 80, 230, 140); s.gnd(230, 140); s.text(246, 118, 'tap 6 only: 510 kHz node pole', 'start', 'valsm')
    s.box(360, 55, 220, 50, 'STAGE1', ['single pole, GBW 18 / 5.7 MHz'])
    s.wire((250, 80), (360, 80))
    s.wire((580, 80), (610, 80))
    s.box(610, 55, 200, 50, 'DOWNSTREAM', ['AAF R, C under test'])
    s.wire((810, 80), (840, 80)); s.dot(840, 80); s.text(848, 84, 'out', 'start', 'node')
    s.text(60, 30, '.ac 1 kHz–20 MHz and .tran (10 % → 100 % FS) on chains A/B and C; no ladder, no switches', 'start', 'note')
    return s.svg(900, 230, 'Standalone chain for the anti-alias filter sweep: a source, an optional RC for tap 6 node pole, a '
                           'single-pole stage 1 and the downstream block with the filter under test')


def timeline():
    """the timeline every ladder deck follows (gen_decks / characterize); events evenly spaced, not to scale"""
    s = S()
    ev = [(0, 'start (uic), tap 1 on'), (5, "T_CFG: the deck's tap"), (10, 'follower settled'), (12, 'DUT ramp starts'),
          (17, 'DUT at its level'), (31, 'noise sources on'), (40, 'TEV: switch, event'), (60, 'T_STEP / T_UP: step'),
          (160, 'T_DN: step back'), (200, 'stop (tran, bw)')]
    x0, x1, y = 100, 830, 120
    s.wire((x0, y), (x1, y))
    for i, (t, lab) in enumerate(ev):
        x = x0 + (x1 - x0) * i / (len(ev) - 1)
        s.wire((x, y - 6), (x, y + 6))
        s.text(x, y + 24, f'{t:g} µs', 'middle', 'lbl')
        yy = y - 22 - 22 * (i % 3)
        s.wire((x, y - 6), (x, yy + 5), cls='w para')
        s.text(x, yy, lab, 'middle', 'valsm')
    s.text(x0, 180, 'Not to scale. lin: 0 A held 17–100 µs, then 7 levels × 40 µs; noise runs 2.05 ms (samples from 100 µs); walks 250 µs.', 'start', 'note')
    return s.svg(920, 200, 'Timeline of a ladder deck: start from initial conditions on tap 1, move to the deck tap at 5 microseconds, '
                           'ramp the DUT current in from 12 to 17, events at 40 and 60 microseconds')


def switch_timing():
    """ADC-synchronous range switch (WU-0005): every edge timed from the ADC's sampling clock"""
    s = S()
    x0, us = 320, 260.0                     # x of sample n, px per us
    X = lambda t: x0 + t * us
    rows = [('ADC samples', 60), ('EN_b (MAKE)', 120), ('EN_a (BREAK)', 170), ('Qi (3↔4 only)', 220), ('Reading', 290)]
    for name, y in rows:
        s.text(20, y + 4, name, 'start', 'lbl')
    # sample instants n-1 .. n+4
    for k in range(-1, 5):
        x = X(0.5 * k)
        s.wire((x, 48), (x, 72))
        s.add(f'<polygon class="arrow" points="{x - 4},{48} {x + 4},{48} {x},{56}"/>')
        s.text(x, 40, f'n{k:+d}' if k else 'n', 'middle', 'valsm')
        s.wire((x, 80), (x, 320), cls='w para')
    s.wire((X(-0.6), 72), (X(2.1), 72))
    # MAKE at sample n + 30 ns, BREAK 50 ns later
    tm, tb = 0.03, 0.08
    s.wire((X(-0.6), 132), (X(tm), 132), (X(tm), 108), (X(2.1), 108))
    s.wire((X(-0.6), 158), (X(tb), 158), (X(tb), 182), (X(2.1), 182))
    s.text(X(tm) + 4, 102, 'MAKE', 'start', 'valsm'); s.text(X(tb) + 4, 196, 'BREAK +50 ns', 'start', 'valsm')
    # Qi opens ~0.55 us after BREAK (enable network); on 3->4 only
    tq = tb + 0.55
    s.wire((X(-0.6), 208), (X(tq), 208), (X(tq), 232), (X(2.1), 232))
    s.text(X(tq) + 4, 246, 'Qi off ~0.55 µs later', 'start', 'valsm')
    # reading source bar
    s.add(f'<rect class="box" x="{X(-0.6)}" y="276" width="{X(0) - X(-0.6)}" height="28" rx="2"/>')
    s.text((X(-0.6) + X(0)) / 2, 294, 'old tap', 'middle', 'valsm')
    s.add(f'<rect class="box" x="{X(0)}" y="276" width="{X(1.5) - X(0)}" height="28" rx="2" style="fill:#dbe8f3"/>')
    s.text((X(0) + X(1.5)) / 2, 294, 'bridge chain, or gain-corrected chain − correction vector', 'middle', 'valsm')
    s.add(f'<rect class="box" x="{X(1.5)}" y="276" width="{X(2.1) - X(1.5)}" height="28" rx="2"/>')
    s.text((X(1.5) + X(2.1)) / 2, 294, 'new tap', 'middle', 'valsm')
    s.text(20, 350, 'The switch edges fall just after a sample and are done well before the next; each switch type always lands at', 'start', 'note')
    s.text(20, 368, 'the same phase of the sample clock, so its correction is one fixed vector of samples, indexed from sample n.', 'start', 'note')
    return s.svg(880, 380, 'ADC-synchronous range switch: MAKE just after sample n, BREAK 50 nanoseconds later, Qi on 3 to 4 '
                           'about half a microsecond later; the reading comes from a bridge chain or a corrected chain until the new tap settles')


def dsp_pipeline():
    """the per-sample digital compensation in the FPGA, from the three current ADCs to the reading"""
    s = S()
    stages = [('3 current ADCs', ['2 MS/s, same edge', 'as the voltage ADC']),
              ('Chain select', ['owner chain, or', 'a bridge chain']),
              ('Calibrate', ['offset and gain', 'per tap (2 points)']),
              ('Switch correction', ['÷ R_eff(t),', '− a(n) − b(n)·Î']),
              ('Timestamp', ['− group delay', 'of the chain']),
              ('Use', ['I × V, charge,', 'average / decimate'])]
    w, h, gap, y = 140, 70, 18, 40
    for i, (title, lines) in enumerate(stages):
        x = 16 + i * (w + gap)
        s.box(x, y, w, h, title, lines, cls='box')
        if i:
            xa = x - gap
            s.wire((xa, y + h / 2), (x - 6, y + h / 2))
            s.add(f'<polygon class="arrow" points="{x - 6},{y + h / 2 - 4} {x - 6},{y + h / 2 + 4} {x},{y + h / 2}"/>')
    s.text(16, y + h + 30, 'Per-unit tables: six offsets and gains, the chains\' step response s(t), and two correction vectors', 'start', 'note')
    s.text(16, y + h + 48, 'per switch type (~30 samples each). The range comparators and tap enables run alongside.', 'start', 'note')
    return s.svg(16 * 2 + 6 * w + 5 * gap, 170, 'Digital compensation pipeline: ADCs, chain select, per-tap calibration, '
                 'range-switch correction, timestamp shift by group delay, then power, charge and averaging')


if __name__ == '__main__':
    for doc, name, fn in (('tr-0002-afe1-10-analog-front-end', 'fig-front-end', front_end),
                          ('tr-0002-afe1-10-analog-front-end', 'fig-boot-why', boot_why),
                          ('tr-0002-afe1-10-analog-front-end', 'fig-guard-mechanism', mechanism),
                          ('tr-0002-afe1-10-analog-front-end', 'fig-enable-logic', enable_logic),
                          ('tr-0002-afe1-10-analog-front-end', 'fig-chain', chain),
                          ('tr-0002-afe1-10-analog-front-end', 'fig-front-end', front_end),
                          ('tr-0002-afe1-10-analog-front-end', 'fig-chain', chain),
                          ('tr-0002-afe1-10-analog-front-end', 'fig-bench', bench),
                          ('tr-0002-afe1-10-analog-front-end', 'fig-dut-bench', dut_bench),
                          ('tr-0002-afe1-10-analog-front-end', 'fig-noise-bench', noise_bench),
                          ('tr-0002-afe1-10-analog-front-end', 'fig-aaf-bench', aaf_bench),
                          ('tr-0002-afe1-10-analog-front-end', 'fig-timeline', timeline),
                          ('tr-0002-afe1-10-analog-front-end', 'fig-chain', chain),
                          ('tr-0002-afe1-10-analog-front-end', 'fig-switch-timing', switch_timing),
                          ('tr-0002-afe1-10-analog-front-end', 'fig-dsp', dsp_pipeline)):
        os.makedirs(os.path.join(HERE, doc), exist_ok=True)
        open(os.path.join(HERE, doc, name + '.svg'), 'w').write(fn())
        print('Wrote', f'{doc}/{name}.svg')
