# Wires and connections

## What connects

Two things are connected when they touch:

- a wire **end or corner** lands on a **pin**, on another wire's end or corner, or on the **middle of a wire**
  (a "T");
- a **pin** lies on a wire (a wire may run straight through a pin).

Two wires that merely **cross** are *not* connected. Two things far apart are connected when they carry the same
**net label**.

## Junction dots

A dot is drawn wherever three or more connections meet (a T, a pin with two wires, four wires at a corner). They are
automatic; switch them off for a whole sheet in *View > Toggle junction dots* or the document inspector
(`page.junctions`). The **Junction** symbol forces a dot.

## Wire hops

With *View > Toggle wire hops* (document inspector: *Wire hops*), a horizontal wire jumps over a vertical one with a
small semicircle where they cross without connecting, so crossings never look like connections. Hops are part of the
drawing: exports and TikZ show them too.

## Drawing and editing wires

- `W`, click, click corners, finish on a pin or wire (or press `Enter` / `Esc` / right-click). The elbow follows your
  mouse; `/` flips it between horizontal-first and vertical-first. `Backspace` removes the last corner.
- Ends **snap** to pins and wire ends first, then to the middle of wires, then to the grid; a ring shows the snap.
- **Stretch** an end by dragging it; **slide** a segment by dragging its middle; `Alt`-drag moves the whole wire;
  double-click a segment to add a corner.
- Moving a part drags the wires attached to its pins and any wires teeing into them.

## Naming nets

| Symbol | Python | Names the net… |
|---|---|---|
| **Net label** (`L`) | `s.flag(at, 'CLK', side='right')` | with its text; same text anywhere = same net |
| **Supply rail** | `s.rail(at, '+5 V')` | with its net name (bar or arrow) |
| **Ground** | `s.gnd(at)` | `0` (the SPICE ground) unless you change *Net* (e.g. `AGND`); earth, signal or chassis drawing |
| **Terminal / port** | `s.terminal(at, 'IN')` | with its label (or *Net*) |

Unnamed nets get automatic names `N001`, `N002`, … (never reusing a name a label already took). Net names accept
[text markup](Text-Markup.md): the label shows `V_{OUT}` as V<sub>OUT</sub> and the netlist uses `VOUT`.

- **No-connect mark**: put it on a pin you leave open on purpose; the unconnected-pin warning skips it.
- **Test point**, **Probe**: parts that sit on a net (test points get a reference, TP1…).

## Buses

A bus carries several signals as one thick wire.

1. **Draw a bus**: pick the bus line style (the thickest of the line-style buttons) or set a wire's style to *Bus*. A
   wire started on a bus pin, or on an existing bus, becomes a bus by itself.
2. **Name it** with a net label on the bus: `D[7:0]` (or `D[0..7]`). Its members are the nets `D0` … `D7`.
3. **Connect parts**: a component's bus pin (a register's `D[7:0]` with *Bus pins* on, a multiplexer's data inputs
   when *Data width* > 1, a custom logic IC's `[n]` pins) connects bit by bit: bit *i* of the pin joins `D`*i*.
   In the netlist these appear as pins `D0` … `D7` of the part.
4. **Tap single bits** with the **Bus entry** symbol (the 45° stub) and a net label on the tapped wire: a wire labelled
   `D3` is bit 3 of the bus. Any wire elsewhere labelled `D3` is the same net.

Rules:

- A plain wire that only touches a bus is **not** connected to it (as in KiCad): connections between bus and single
  wires go through names.
- Buses with the same base name (`D[7:0]` here, `D[7:0]` there) are one bus.
- An **unlabelled** bus between two bus pins still connects them bit by bit (its members are named `BUS1_0`, …).
- A width mismatch (an 8-bit pin on a `D[3:0]` bus) is reported in the netlist warnings.

![Bus example](img/symbols/busentry.svg)

See `examples/digital/bus-breakout.py` and `examples/digital/accumulator.py`.

## Net warnings

The Netlist pane and every netlist export list:

- unconnected pins (a pin alone on its net), except those with a no-connect mark;
- a net named twice (two different labels on one net);
- bus width mismatches.
