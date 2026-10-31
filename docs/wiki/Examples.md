# Examples

The `examples/` folder ships with Schematrix and is copied into your workspace (`~/Schematrix/examples`), so
**File > Open** lists them. Each example is a Python script with the documents it makes beside it as `.json` files:
open the `.json` to edit the drawing, or open the `.py` in the Script pane to see how it was built. New versions add new
examples to your workspace without touching files you changed or deleted.

## analog

| Example | |
|---|---|
| `inverting-amplifier` | gain −10 op-amp stage; simulates (`.tran`, `.ac`) |
| `sallen-key-lowpass` | 2nd-order Butterworth low-pass, f<sub>c</sub> = 1 kHz; `.ac` |
| `instrumentation-bridge` | strain-gauge quarter bridge into an instrumentation amplifier; nets by label |
| `photodiode-tia` | transimpedance amplifier with R<sub>F</sub> ∥ C<sub>F</sub> |
| `common-emitter` | BJT amplifier with divider bias; simulates |

## digital

| Example | |
|---|---|
| `sr-latch` | cross-coupled NAND latch, with wire hops |
| `full-adder` | gate-level full adder in the input-rail layout |
| `counter-decoder` | 3-bit counter into a 3:8 decoder over a bus |
| `shift-register-leds` | SIPO shift register driving an LED bank by net labels |
| `debounce` | push button, RC and a Schmitt inverter |
| `accumulator` | 8-bit adder + register datapath with buses |
| `bus-breakout` | bus labels, bus entries, bit-by-bit connections |

## power

| Example | |
|---|---|
| `linear-supply` | transformer, bridge rectifier, reservoir capacitor, 7805 regulator |
| `buck-converter` | P-MOSFET buck converter; simulates the start-up |
| `relay-driver` | NPN low-side relay driver with flyback diode |
| `load-switch` | high-side P-MOSFET load switch with level shifter |

## simulation

Each prints `.meas` results when run with ngspice; see [Simulation](Simulation.md#worked-examples).

| Example | |
|---|---|
| `rc-step` | RC step response at 1τ and 5τ |
| `rlc-resonance` | series RLC: peak and resonant frequency |
| `half-wave-rectifier` | ripple on a reservoir capacitor |
| `cmos-inverter` | DC transfer curve and switching threshold |
| `opamp-integrator` | square wave in, triangle out |
| `diode-clipper` | antiparallel diodes clamping a sine |

## misc

| Example | |
|---|---|
| `tube-preamp` | 12AX7 common-cathode stage in the `formal` style |
| `signal-chain` | sensor → amplifier → filter → ADC → MCU block diagram |
| `paper-figure` | a difference amplifier styled for a LaTeX paper |
| `markup-and-styles` | one circuit in every theme, with text markup |

## netlists

SPICE and KiCad files to try *File > Import netlist* on, including `foreign-kicad-sample.net` (a KiCad export) and
`colpitts-oscillator.cir` (a plain SPICE deck).

## tr-0002

`schematics.py` is an original Instrix documentation figure script, written against a hand-rolled `S` class. Run it in the Script
pane and its 12 figures open as editable tabs; or run it with Python to write the SVGs it always wrote. See
[Legacy figure scripts](Legacy-Figure-Scripts.md).

## Regenerating

`python scripts/build_examples.py` re-runs every example script and rewrites the `.json` documents and the sample
netlists.
