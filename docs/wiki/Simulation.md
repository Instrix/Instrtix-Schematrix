# Simulation

Schematrix does not simulate by itself; it writes SPICE netlists that [ngspice](https://ngspice.sourceforge.io/)
(free; `sudo apt install ngspice`), LTspice or any other SPICE can run. A sheet can carry everything a simulation
needs: sources, analyses, models and measurements.

## 1. Draw with simulatable parts

Resistors, capacitors, inductors, diodes, BJTs, MOSFETs, JFETs, voltage / current sources, dependent sources
(E, G, H, F), op-amps and subcircuit blocks have SPICE templates (see [Netlists](Netlists.md#spice-templates)). Parts
without one (relays, logic, tubes, …) are written as comments and ignored by the simulator.

- **Values** in engineering notation: `10 k\ohm`, `4.7 \uF`, `100n` (see [Text markup](Text-Markup.md) for Ω and µ).
- **Sources**: a plain number is DC (`12`) or, for AC kinds, an AC magnitude; or write the SPICE spec as the value:
  `SIN(0 100m 1k)`, `PULSE(0 5 0 1n 1n 50u 100u)`, `AC 1`.
- **Ground**: the ground symbol's net is `0`, the SPICE reference node.
- **Name the nets you want to look at** with net labels (`OUT`); they keep their names in the netlist.

## 2. Add analyses

With nothing selected, the document inspector has **SPICE lines**: one line each, written to the end of the netlist.
In Python: `s.directive('.tran 10u 5m', '.ac dec 20 10 1Meg')`.

| Line | |
|---|---|
| `.op` | DC operating point |
| `.tran 10u 5m` | transient: step 10 µs, stop at 5 ms (`uic` to start from zero) |
| `.ac dec 50 10 100k` | AC sweep, 50 points per decade from 10 Hz to 100 kHz |
| `.dc V1 0 5 0.01` | DC sweep of a source |
| `.meas tran vmax MAX v(OUT)` | a measurement printed when the run ends |
| `.meas ac f0 WHEN vp(OUT)=0` | e.g. the frequency where the phase crosses 0 |
| `.model 2N3904 NPN(Bf=300 …)`, `.include models.lib`, `.param R=1k` | models, libraries, parameters |

`.save all` is added for you when there is an `.ac` analysis and no `.save` line (ngspice in batch mode otherwise keeps
no AC data).

## 3. Models

Parts use their **Part number** as the model name (`2N3904`, `1N4148`). Without one, a default model is written into
the netlist, good enough for first results:

| Model | Used by | |
|---|---|---|
| `DMOD` | diodes | 1N4148-like |
| `NPN`, `PNP` | BJTs | β ≈ 200 |
| `NMOS`, `PMOS` | MOSFETs | level 1, V<sub>th</sub> ±1.5 V |
| `NJF`, `PJF` | JFETs | |
| `OPAMP` | op-amps (3 pins) | gain 10⁵, GBW 1 MHz, 100 Ω output |
| `OPAMP5` | op-amps with supply pins | the same, output clamped between the supplies |

A `.model` / `.subckt` of the same name in your SPICE lines replaces the default. For real parts, set the Part number
and `.include` the manufacturer's model file.

## 4. Run it

```bash
schematrix netlist amplifier.json -o amplifier.cir      # or Export > Netlist: SPICE in the editor
ngspice -b amplifier.cir                                # batch: prints the .meas results
ngspice amplifier.cir                                   # interactive: then  plot v(out)
```

From Python:

```python
import subprocess
open('amp.cir', 'w').write(s.spice())
print(subprocess.run(['ngspice', '-b', 'amp.cir'], capture_output=True, text=True).stdout)
```

## Worked examples

`examples/simulation/` holds sheets whose `.meas` results match the textbook (checked with ngspice):

| Example | Measures | Result |
|---|---|---|
| RC step response | output at 1τ and 5τ | 0.632 V, 0.993 V |
| RLC resonance | peak and resonant frequency | 5.03 kHz, Q = 10 |
| Half-wave rectifier | ripple | 1.5 V |
| CMOS inverter | switching threshold | 2.33 V |
| Op-amp integrator | triangle amplitude | 0.51 V<sub>pp</sub> |
| Diode clipper | clamp levels | ±0.65 V |

Also `analog/inverting-amplifier`, `analog/sallen-key-lowpass`, `analog/common-emitter` and `power/buck-converter`
carry analyses. See [Examples](Examples.md).

## Importing a SPICE deck

*File > Import netlist* reads a `.cir` deck into a new sheet and keeps its analyses, models and subcircuits as the
sheet's SPICE lines, so exporting it again gives a runnable deck (see [Netlists](Netlists.md)).
