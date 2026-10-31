# Symbol library

Every built-in symbol, generated from the library itself (`python scripts/build_wiki_symbols.py`).
In Python each symbol is a method of `Schematic` (`s.resistor(...)`), and so is each named variant
(`s.zener(...)`). Settings marked *shape* change the drawing; the others are information.

Every part also has **Reference**, **Value** and **Part number**, and can carry any number of
[fields](Fields-and-Properties.md). Pins are named as listed; the netlist uses these names.

**Categories:** [Passive](#passive) · [Semiconductor](#semiconductor) · [Analog](#analog) · [Logic](#logic) · [Sources](#sources) · [Loads & meters](#loads--meters) · [Electromechanical](#electromechanical) · [Vacuum tubes](#vacuum-tubes) · [Signal flow](#signal-flow) · [Generic](#generic) · [Nets](#nets)

## Passive

### Capacitor

<img src="img/symbols/capacitor.svg" alt="Capacitor" height="70">

- **Python:** `s.capacitor(...)`  ·  **Reference prefix:** `C`  ·  **SPICE:** `C {1} {2} {value}`
- **Pins:** `1`, `2`
- **Suggested fields:** Voltage rating, Tolerance, Dielectric, ESR

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `40` | *shape* pin-to-pin distance |
| `polarized` (Polarized) | bool | `False` | *shape*  |
| `plate` (Negative plate) | enum: flat, curved | `flat` | *shape* curved: electrolytic style |

**Named variants** (each has its own palette tile and Python method):

| | Variant | Python | Same as |
|---|---|---|---|
| <img src="img/symbols/capacitor_polarized.svg" height="48"> | Capacitor, polarized | `s.capacitor_polarized()` | `capacitor` with polarized=True |
| <img src="img/symbols/electrolytic.svg" height="48"> | Electrolytic capacitor | `s.electrolytic()` | `capacitor` with polarized=True, plate='curved' |

### Crystal

<img src="img/symbols/crystal.svg" alt="Crystal" height="70">

- **Python:** `s.crystal(...)`  ·  **Reference prefix:** `Y`
- **Pins:** `1`, `2`
- **Suggested fields:** Load capacitance, Tolerance, ESR

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `60` | *shape* pin-to-pin distance |

### Current shunt (Kelvin)

<img src="img/symbols/shunt.svg" alt="Current shunt (Kelvin)" height="70">

- **Python:** `s.shunt(...)`  ·  **Reference prefix:** `R`  ·  **SPICE:** `R {1} {2} {value}`
- **Pins:** `1`, `2`, `S1`, `S2`
- **Suggested fields:** Tolerance, Power, Tempco, Voltage rating

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `60` | *shape* pin-to-pin distance |

### Ferrite bead

<img src="img/symbols/ferrite.svg" alt="Ferrite bead" height="70">

- **Python:** `s.ferrite(...)`  ·  **Reference prefix:** `FB`  ·  **SPICE:** `L {1} {2} {value}`
- **Pins:** `1`, `2`
- **Suggested fields:** Impedance @100MHz, Current rating

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `40` | *shape* pin-to-pin distance |

### Fuse

<img src="img/symbols/fuse.svg" alt="Fuse" height="70">

- **Python:** `s.fuse(...)`  ·  **Reference prefix:** `F`  ·  **SPICE:** `R {1} {2} 10m`
- **Pins:** `1`, `2`
- **Suggested fields:** Current rating, Voltage rating, Speed

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `60` | *shape* pin-to-pin distance |

### Inductor

<img src="img/symbols/inductor.svg" alt="Inductor" height="70">

- **Python:** `s.inductor(...)`  ·  **Reference prefix:** `L`  ·  **SPICE:** `L {1} {2} {value}`
- **Pins:** `1`, `2`
- **Suggested fields:** Current rating, Saturation current, DCR, Tolerance

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `60` | *shape* pin-to-pin distance |
| `body` (Body) | num | `40` | *shape*  |
| `core` (Core) | enum: air, iron, ferrite | `air` | *shape*  |

### Photoresistor (LDR)

<img src="img/symbols/ldr.svg" alt="Photoresistor (LDR)" height="70">

- **Python:** `s.ldr(...)`  ·  **Reference prefix:** `R`  ·  **SPICE:** `R {1} {2} {value}`
- **Pins:** `1`, `2`

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `60` | *shape* pin-to-pin distance |
| `body` (Body) | num | `36` | *shape*  |
| `shape` (Shape) | enum: zigzag, iec | `zigzag` | *shape*  |

### Potentiometer

<img src="img/symbols/potentiometer.svg" alt="Potentiometer" height="70">

- **Python:** `s.potentiometer(...)`  ·  **Reference prefix:** `RV`
- **Pins:** `1`, `2`, `W`
- **Suggested fields:** Tolerance, Power, Tempco, Voltage rating

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `60` | *shape* pin-to-pin distance |
| `body` (Body) | num | `36` | *shape*  |
| `kind` (Kind) | enum: pot, trimmer | `pot` | *shape*  |

### Resistor

<img src="img/symbols/resistor.svg" alt="Resistor" height="70">

- **Python:** `s.resistor(...)`  ·  **Reference prefix:** `R`  ·  **SPICE:** `R {1} {2} {value}`
- **Pins:** `1`, `2`
- **Suggested fields:** Tolerance, Power, Tempco, Voltage rating

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `60` | *shape* pin-to-pin distance |
| `body` (Body) | num | `36` | *shape*  |
| `shape` (Shape) | enum: zigzag, iec | `zigzag` | *shape*  |

### Spark gap / GDT

<img src="img/symbols/spark_gap.svg" alt="Spark gap / GDT" height="70">

- **Python:** `s.spark_gap(...)`  ·  **Reference prefix:** `E`
- **Pins:** `1`, `2`
- **Suggested fields:** Spark-over voltage

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `60` | *shape* pin-to-pin distance |

### Thermistor

<img src="img/symbols/thermistor.svg" alt="Thermistor" height="70">

- **Python:** `s.thermistor(...)`  ·  **Reference prefix:** `TH`  ·  **SPICE:** `R {1} {2} {value}`
- **Pins:** `1`, `2`
- **Suggested fields:** Beta, R25, Tolerance

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `60` | *shape* pin-to-pin distance |
| `kind` (Kind) | enum: ntc, ptc | `ntc` | *shape*  |

### Transformer

<img src="img/symbols/transformer.svg" alt="Transformer" height="70">

- **Python:** `s.transformer(...)`  ·  **Reference prefix:** `T`
- **Pins:** `P1`, `P2`, `S1`, `S2`
- **Suggested fields:** Turns ratio, Power, Isolation

| Setting | Type | Default | |
|---|---|---|---|
| `core` (Core) | enum: air, iron, ferrite | `iron` | *shape*  |
| `ct` (Centre tap) | bool | `False` | *shape*  |
| `dots` (Polarity dots) | bool | `True` | *shape*  |

### Variable capacitor

<img src="img/symbols/cvar.svg" alt="Variable capacitor" height="70">

- **Python:** `s.cvar(...)`  ·  **Reference prefix:** `C`  ·  **SPICE:** `C {1} {2} {value}`
- **Pins:** `1`, `2`
- **Suggested fields:** Voltage rating, Tolerance, Dielectric, ESR

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `40` | *shape* pin-to-pin distance |
| `kind` (Kind) | enum: variable, trimmer | `variable` | *shape*  |

### Variable resistor

<img src="img/symbols/rvar.svg" alt="Variable resistor" height="70">

- **Python:** `s.rvar(...)`  ·  **Reference prefix:** `R`  ·  **SPICE:** `R {1} {2} {value}`
- **Pins:** `1`, `2`
- **Suggested fields:** Tolerance, Power, Tempco, Voltage rating

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `60` | *shape* pin-to-pin distance |
| `body` (Body) | num | `36` | *shape*  |
| `shape` (Shape) | enum: zigzag, iec | `zigzag` | *shape*  |

### Varistor (VDR)

<img src="img/symbols/varistor.svg" alt="Varistor (VDR)" height="70">

- **Python:** `s.varistor(...)`  ·  **Reference prefix:** `RV`  ·  **SPICE:** `R {1} {2} {value}`
- **Pins:** `1`, `2`
- **Suggested fields:** Clamping voltage, Energy

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `60` | *shape* pin-to-pin distance |

## Semiconductor

### Bridge rectifier

<img src="img/symbols/bridge.svg" alt="Bridge rectifier" height="70">

- **Python:** `s.bridge(...)`  ·  **Reference prefix:** `D`
- **Pins:** `AC1`, `AC2`, `+`, `-`
- **Suggested fields:** Reverse voltage, Forward current, Forward voltage, Power

### Darlington (NPN)

<img src="img/symbols/darlington.svg" alt="Darlington (NPN)" height="70">

- **Python:** `s.darlington(...)`  ·  **Reference prefix:** `Q`
- **Pins:** `C`, `B`, `E`
- **Suggested fields:** Vce max, Ic max, hFE, Power

### Diac

<img src="img/symbols/diac.svg" alt="Diac" height="70">

- **Python:** `s.diac(...)`  ·  **Reference prefix:** `D`
- **Pins:** `MT1`, `MT2`

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `60` | *shape* pin-to-pin distance |

### Diode

<img src="img/symbols/diode.svg" alt="Diode" height="70">

- **Python:** `s.diode(...)`  ·  **Reference prefix:** `D`  ·  **SPICE:** `D {A} {K} {model}`
- **Pins:** `A`, `K`
- **Suggested fields:** Reverse voltage, Forward current, Forward voltage, Power

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `60` | *shape* pin-to-pin distance |
| `kind` (Kind) | enum: standard, schottky, zener, avalanche, tvs, tvs_uni, led, photodiode, varactor, tunnel, pin, laser, step_recovery, shockley | `standard` | *shape*  |

**Named variants** (each has its own palette tile and Python method):

| | Variant | Python | Same as |
|---|---|---|---|
| <img src="img/symbols/zener.svg" height="48"> | Zener diode | `s.zener()` | `diode` with kind='zener' |
| <img src="img/symbols/schottky.svg" height="48"> | Schottky diode | `s.schottky()` | `diode` with kind='schottky' |
| <img src="img/symbols/led.svg" height="48"> | LED | `s.led()` | `diode` with kind='led' |
| <img src="img/symbols/tvs_diode.svg" height="48"> | TVS diode | `s.tvs_diode()` | `diode` with kind='tvs_uni' |
| <img src="img/symbols/tvs_bidirectional.svg" height="48"> | TVS diode, bidirectional | `s.tvs_bidirectional()` | `diode` with kind='tvs' |
| <img src="img/symbols/avalanche_diode.svg" height="48"> | Avalanche diode | `s.avalanche_diode()` | `diode` with kind='avalanche' |
| <img src="img/symbols/photodiode.svg" height="48"> | Photodiode | `s.photodiode()` | `diode` with kind='photodiode' |
| <img src="img/symbols/varactor.svg" height="48"> | Varactor (varicap) | `s.varactor()` | `diode` with kind='varactor' |
| <img src="img/symbols/tunnel_diode.svg" height="48"> | Tunnel diode | `s.tunnel_diode()` | `diode` with kind='tunnel' |
| <img src="img/symbols/pin_diode.svg" height="48"> | PIN diode | `s.pin_diode()` | `diode` with kind='pin' |
| <img src="img/symbols/laser_diode.svg" height="48"> | Laser diode | `s.laser_diode()` | `diode` with kind='laser' |
| <img src="img/symbols/step_recovery_diode.svg" height="48"> | Step-recovery diode | `s.step_recovery_diode()` | `diode` with kind='step_recovery' |
| <img src="img/symbols/shockley_diode.svg" height="48"> | Shockley (4-layer) diode | `s.shockley_diode()` | `diode` with kind='shockley' |

### IGBT

<img src="img/symbols/igbt.svg" alt="IGBT" height="70">

- **Python:** `s.igbt(...)`  ·  **Reference prefix:** `Q`
- **Pins:** `C`, `G`, `E`
- **Suggested fields:** Vce max, Ic max, Vce(sat)

| Setting | Type | Default | |
|---|---|---|---|
| `body_diode` (Freewheel diode) | bool | `False` | *shape*  |

### N-JFET

<img src="img/symbols/njfet.svg" alt="N-JFET" height="70">

- **Python:** `s.njfet(...)`  ·  **Reference prefix:** `Q`  ·  **SPICE:** `J {D} {G} {S} {model}`
- **Pins:** `D`, `G`, `S`

### N-MOSFET

<img src="img/symbols/nmos.svg" alt="N-MOSFET" height="70">

- **Python:** `s.nmos(...)`  ·  **Reference prefix:** `Q`  ·  **SPICE:** `M {D} {G} {S} {B|S} {model}`
- **Pins:** `D`, `G`, `S`
- **Suggested fields:** Vds max, Id max, Rds(on), Vgs(th)

| Setting | Type | Default | |
|---|---|---|---|
| `body_diode` (Body diode) | bool | `False` | *shape*  |
| `mode` (Mode) | enum: enhancement, depletion | `enhancement` | *shape*  |
| `bulk` (Bulk pin) | bool | `False` | *shape* 4-terminal: separate body connection |

### NPN transistor

<img src="img/symbols/npn.svg" alt="NPN transistor" height="70">

- **Python:** `s.npn(...)`  ·  **Reference prefix:** `Q`  ·  **SPICE:** `Q {C} {B} {E} {model}`
- **Pins:** `C`, `B`, `E`
- **Suggested fields:** Vce max, Ic max, hFE, Power

| Setting | Type | Default | |
|---|---|---|---|
| `envelope` (Circle) | bool | `False` | *shape*  |
| `photo` (Phototransistor) | bool | `False` | *shape*  |

### Optocoupler

<img src="img/symbols/optocoupler.svg" alt="Optocoupler" height="70">

- **Python:** `s.optocoupler(...)`  ·  **Reference prefix:** `U`
- **Pins:** `A`, `K`, `C`, `E`
- **Suggested fields:** CTR, Isolation

| Setting | Type | Default | |
|---|---|---|---|
| `output` (Output) | enum: transistor, triac | `transistor` | *shape*  |

### P-JFET

<img src="img/symbols/pjfet.svg" alt="P-JFET" height="70">

- **Python:** `s.pjfet(...)`  ·  **Reference prefix:** `Q`  ·  **SPICE:** `J {D} {G} {S} {model}`
- **Pins:** `D`, `G`, `S`

### P-MOSFET

<img src="img/symbols/pmos.svg" alt="P-MOSFET" height="70">

- **Python:** `s.pmos(...)`  ·  **Reference prefix:** `Q`  ·  **SPICE:** `M {D} {G} {S} {B|S} {model}`
- **Pins:** `D`, `G`, `S`
- **Suggested fields:** Vds max, Id max, Rds(on), Vgs(th)

| Setting | Type | Default | |
|---|---|---|---|
| `body_diode` (Body diode) | bool | `False` | *shape*  |
| `mode` (Mode) | enum: enhancement, depletion | `enhancement` | *shape*  |
| `bulk` (Bulk pin) | bool | `False` | *shape* 4-terminal: separate body connection |

### PNP transistor

<img src="img/symbols/pnp.svg" alt="PNP transistor" height="70">

- **Python:** `s.pnp(...)`  ·  **Reference prefix:** `Q`  ·  **SPICE:** `Q {C} {B} {E} {model}`
- **Pins:** `C`, `B`, `E`
- **Suggested fields:** Vce max, Ic max, hFE, Power

| Setting | Type | Default | |
|---|---|---|---|
| `envelope` (Circle) | bool | `False` | *shape*  |
| `photo` (Phototransistor) | bool | `False` | *shape*  |

### Thyristor (SCR)

<img src="img/symbols/scr.svg" alt="Thyristor (SCR)" height="70">

- **Python:** `s.scr(...)`  ·  **Reference prefix:** `D`
- **Pins:** `A`, `K`, `G`
- **Suggested fields:** Reverse voltage, Forward current, Forward voltage, Power

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `60` | *shape* pin-to-pin distance |

### Triac

<img src="img/symbols/triac.svg" alt="Triac" height="70">

- **Python:** `s.triac(...)`  ·  **Reference prefix:** `Q`
- **Pins:** `MT1`, `MT2`, `G`

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `60` | *shape* pin-to-pin distance |

## Analog

### Fully differential amp

<img src="img/symbols/fdamp.svg" alt="Fully differential amp" height="70">

- **Python:** `s.fdamp(...)`  ·  **Reference prefix:** `U`
- **Pins:** `inp`, `inm`, `outm`, `outp`, `vocm`
- **Suggested fields:** GBW, Supply range

| Setting | Type | Default | |
|---|---|---|---|
| `vocm` (VOCM pin) | bool | `True` | *shape*  |

### Instrumentation amp

<img src="img/symbols/inamp.svg" alt="Instrumentation amp" height="70">

- **Python:** `s.inamp(...)`  ·  **Reference prefix:** `U`
- **Pins:** `inm`, `inp`, `out`, `rg1`, `rg2`, `ref`
- **Suggested fields:** Gain, CMRR, Supply range

| Setting | Type | Default | |
|---|---|---|---|
| `rg` (Gain pins (RG)) | bool | `True` | *shape*  |

### Op-amp

<img src="img/symbols/opamp.svg" alt="Op-amp" height="70">

- **Python:** `s.opamp(...)`  ·  **Reference prefix:** `U`  ·  **SPICE:** `X {inp} {inm} {vp?} {vn?} {out} {model}`
- **Pins:** `inm`, `inp`, `out`
- **Suggested fields:** GBW, Slew rate, Supply range, Offset

| Setting | Type | Default | |
|---|---|---|---|
| `top` (Top input) | enum: -, + | `-` | *shape*  |
| `supply` (Supply pins) | bool | `False` | *shape*  |
| `comparator` (Comparator) | bool | `False` | *shape* draws the step mark |

### Sensor (generic)

<img src="img/symbols/sensor.svg" alt="Sensor (generic)" height="70">

- **Python:** `s.sensor(...)`  ·  **Reference prefix:** `U`
- **Pins:** `1`, `2`
- **Suggested fields:** Range, Accuracy, Interface

| Setting | Type | Default | |
|---|---|---|---|
| `quantity` (Quantity) | str | `T` | *shape* letter or short text inside, e.g. T, P, B, RH |

### Shunt reference (TL431)

<img src="img/symbols/vref.svg" alt="Shunt reference (TL431)" height="70">

- **Python:** `s.vref(...)`  ·  **Reference prefix:** `U`
- **Pins:** `K`, `A`, `REF`
- **Suggested fields:** Reference voltage, Tolerance

### Voltage regulator

<img src="img/symbols/regulator.svg" alt="Voltage regulator" height="70">

- **Python:** `s.regulator(...)`  ·  **Reference prefix:** `U`  ·  **SPICE:** `X {IN} {GND} {OUT} {model}`
- **Pins:** `IN`, `OUT`, `GND`
- **Suggested fields:** Output voltage, Dropout, Max current

| Setting | Type | Default | |
|---|---|---|---|
| `kind` (Kind) | enum: fixed, adjustable | `fixed` | *shape*  |
| `enable` (Enable pin) | bool | `False` | *shape*  |

## Logic

### Adder

<img src="img/symbols/adder.svg" alt="Adder" height="70">

- **Python:** `s.adder(...)`  ·  **Reference prefix:** `U`
- **Pins:** `A0`, `A1`, `A2`, `A3`, `B0`, `B1`, `B2`, `B3`, `CI`, `S0`, `S1`, `S2`, `S3`, `CO`

| Setting | Type | Default | |
|---|---|---|---|
| `bits` (Bits) | num | `4` | *shape* port width in bits |
| `carry_in` (Carry in) | bool | `True` | *shape*  |
| `carry_out` (Carry out) | bool | `True` | *shape*  |
| `bus` (Bus pins) | bool | `False` | *shape* one thick bus pin per port instead of one pin per bit |

**Named variants** (each has its own palette tile and Python method):

| | Variant | Python | Same as |
|---|---|---|---|
| <img src="img/symbols/adder4.svg" height="48"> | Adder, 4-bit | `s.adder4()` | `adder` with the defaults |

### Buffer / inverter

<img src="img/symbols/buffer.svg" alt="Buffer / inverter" height="70">

- **Python:** `s.buffer(...)`  ·  **Reference prefix:** `U`
- **Pins:** `in`, `out`

| Setting | Type | Default | |
|---|---|---|---|
| `invert` (Inverting) | bool | `False` | *shape*  |
| `size` (Size) | num | `22` | *shape*  |
| `schmitt` (Schmitt trigger) | bool | `False` | *shape*  |
| `tristate` (Tri-state (OE pin)) | bool | `False` | *shape*  |
| `shape` (Shape) | enum: ansi, iec | `ansi` | *shape* ansi: distinctive shapes; iec: rectangles with &, ≥1, =1, 1 |

**Named variants** (each has its own palette tile and Python method):

| | Variant | Python | Same as |
|---|---|---|---|
| <img src="img/symbols/buffer_gate.svg" height="48"> | Buffer | `s.buffer_gate()` | `buffer` with the defaults |
| <img src="img/symbols/not_gate.svg" height="48"> | NOT gate (inverter) | `s.not_gate()` | `buffer` with invert=True |
| <img src="img/symbols/schmitt_inverter.svg" height="48"> | Schmitt inverter | `s.schmitt_inverter()` | `buffer` with invert=True, schmitt=True |
| <img src="img/symbols/schmitt_buffer.svg" height="48"> | Schmitt buffer | `s.schmitt_buffer()` | `buffer` with schmitt=True |
| <img src="img/symbols/tristate_buffer.svg" height="48"> | Tri-state buffer | `s.tristate_buffer()` | `buffer` with tristate=True |

### Counter

<img src="img/symbols/counter.svg" alt="Counter" height="70">

- **Python:** `s.counter(...)`  ·  **Reference prefix:** `U`
- **Pins:** `D0`, `D1`, `D2`, `D3`, `LD`, `EN`, `CLK`, `CLR`, `Q0`, `Q1`, `Q2`, `Q3`, `CO`

| Setting | Type | Default | |
|---|---|---|---|
| `bits` (Bits) | num | `4` | *shape* port width in bits |
| `direction` (Direction) | enum: up, updown | `up` | *shape*  |
| `load` (Parallel load) | bool | `True` | *shape*  |
| `enable` (Count enable) | bool | `True` | *shape*  |
| `clear` (Clear) | bool | `True` | *shape*  |
| `carry` (Carry out) | bool | `True` | *shape*  |
| `bus` (Bus pins) | bool | `False` | *shape* one thick bus pin per port instead of one pin per bit |

**Named variants** (each has its own palette tile and Python method):

| | Variant | Python | Same as |
|---|---|---|---|
| <img src="img/symbols/counter4.svg" height="48"> | Counter, binary | `s.counter4()` | `counter` with the defaults |
| <img src="img/symbols/counter_updown.svg" height="48"> | Counter, up / down | `s.counter_updown()` | `counter` with direction='updown' |
| <img src="img/symbols/ripple_counter.svg" height="48"> | Ripple counter | `s.ripple_counter()` | `counter` with bits=12, load=False, enable=False, carry=False |

### Decoder / demultiplexer

<img src="img/symbols/decoder.svg" alt="Decoder / demultiplexer" height="70">

- **Python:** `s.decoder(...)`  ·  **Reference prefix:** `U`
- **Pins:** `A0`, `A1`, `A2`, `E`, `Y0`, `Y1`, `Y2`, `Y3`, `Y4`, `Y5`, `Y6`, `Y7`

| Setting | Type | Default | |
|---|---|---|---|
| `inputs` (Address bits) | num | `3` | *shape* 1 to 5: 2, 4, 8, 16 or 32 outputs |
| `active_low` (Active-low outputs) | bool | `True` | *shape*  |
| `enable` (Enable) | bool | `True` | *shape*  |
| `bus` (Bus pins) | bool | `False` | *shape* one thick bus pin per port instead of one pin per bit |

**Named variants** (each has its own palette tile and Python method):

| | Variant | Python | Same as |
|---|---|---|---|
| <img src="img/symbols/decoder_2to4.svg" height="48"> | Decoder 2:4 | `s.decoder_2to4()` | `decoder` with inputs=2 |
| <img src="img/symbols/decoder_3to8.svg" height="48"> | Decoder 3:8 | `s.decoder_3to8()` | `decoder` with the defaults |
| <img src="img/symbols/decoder_4to16.svg" height="48"> | Decoder 4:16 | `s.decoder_4to16()` | `decoder` with inputs=4 |

### Demultiplexer (data)

<img src="img/symbols/demux.svg" alt="Demultiplexer (data)" height="70">

- **Python:** `s.demux(...)`  ·  **Reference prefix:** `U`
- **Pins:** `D`, `S0`, `S1`, `E`, `Y0`, `Y1`, `Y2`, `Y3`

| Setting | Type | Default | |
|---|---|---|---|
| `outputs` (Outputs) | enum: 2, 4, 8, 16 | `4` | *shape*  |
| `width` (Data width) | num | `1` | *shape* bits per port |
| `enable` (Enable) | bool | `True` | *shape*  |
| `bus` (Bus pins) | bool | `False` | *shape* one thick bus pin per port instead of one pin per bit |

### Flip-flop / latch

<img src="img/symbols/flipflop.svg" alt="Flip-flop / latch" height="70">

- **Python:** `s.flipflop(...)`  ·  **Reference prefix:** `U`
- **Pins:** `D`, `CLK`, `Q`, `QN`

| Setting | Type | Default | |
|---|---|---|---|
| `kind` (Kind) | enum: d, jk, t, sr, d-latch | `d` | *shape*  |
| `set_reset` (Async set / reset) | bool | `False` | *shape*  |
| `qbar` (Q̄ output) | bool | `True` | *shape*  |

**Named variants** (each has its own palette tile and Python method):

| | Variant | Python | Same as |
|---|---|---|---|
| <img src="img/symbols/dff.svg" height="48"> | D flip-flop | `s.dff()` | `flipflop` with the defaults |
| <img src="img/symbols/dff_sr.svg" height="48"> | D flip-flop, set / reset | `s.dff_sr()` | `flipflop` with set_reset=True |
| <img src="img/symbols/jkff.svg" height="48"> | JK flip-flop | `s.jkff()` | `flipflop` with kind='jk' |
| <img src="img/symbols/tff.svg" height="48"> | T flip-flop | `s.tff()` | `flipflop` with kind='t' |
| <img src="img/symbols/sr_latch.svg" height="48"> | SR latch | `s.sr_latch()` | `flipflop` with kind='sr' |
| <img src="img/symbols/d_latch.svg" height="48"> | D latch | `s.d_latch()` | `flipflop` with kind='d-latch' |

### Logic IC (custom)

<img src="img/symbols/logic_ic.svg" alt="Logic IC (custom)" height="70">

- **Python:** `s.logic_ic(...)`  ·  **Reference prefix:** `U`
- **Pins:** `D`, `CLK`, `OE`, `Q`
- pins: comma list; ~ = active low (bubble), > = clock, [n] = n-bit bus, empty item = gap

| Setting | Type | Default | |
|---|---|---|---|
| `title` (Function) | str | `IC` | *shape* text inside the top of the body |
| `left` (Left pins) | str | `D[8], , >CLK, ~OE` | *shape*  |
| `right` (Right pins) | str | `Q[8]` | *shape*  |
| `top` (Top pins) | str | `` | *shape*  |
| `bottom` (Bottom pins) | str | `` | *shape*  |
| `bus` (Bus pins) | bool | `True` | *shape* off: expand D[8] into D0..D7 |
| `min_width` (Min width) | num | `40` | *shape*  |

### Logic gate

<img src="img/symbols/gate.svg" alt="Logic gate" height="70">

- **Python:** `s.gate(...)`  ·  **Reference prefix:** `U`
- **Pins:** `in1`, `in2`, `out`

| Setting | Type | Default | |
|---|---|---|---|
| `kind` (Kind) | enum: and, nand, or, nor, xor, xnor | `and` | *shape*  |
| `inputs` (Inputs) | num | `2` | *shape* 2 to 16 |
| `invert_inputs` (Inverted inputs) | str | `` | *shape* input numbers with a bubble, e.g. "1, 3" or "all" |
| `shape` (Shape) | enum: ansi, iec | `ansi` | *shape* ansi: distinctive shapes; iec: rectangles with &, ≥1, =1, 1 |
| `schmitt` (Schmitt inputs) | bool | `False` | *shape*  |

**Named variants** (each has its own palette tile and Python method):

| | Variant | Python | Same as |
|---|---|---|---|
| <img src="img/symbols/and_gate.svg" height="48"> | AND gate | `s.and_gate()` | `gate` with the defaults |
| <img src="img/symbols/nand_gate.svg" height="48"> | NAND gate | `s.nand_gate()` | `gate` with kind='nand' |
| <img src="img/symbols/or_gate.svg" height="48"> | OR gate | `s.or_gate()` | `gate` with kind='or' |
| <img src="img/symbols/nor_gate.svg" height="48"> | NOR gate | `s.nor_gate()` | `gate` with kind='nor' |
| <img src="img/symbols/xor_gate.svg" height="48"> | XOR gate | `s.xor_gate()` | `gate` with kind='xor' |
| <img src="img/symbols/xnor_gate.svg" height="48"> | XNOR gate | `s.xnor_gate()` | `gate` with kind='xnor' |

### Magnitude comparator

<img src="img/symbols/magcomp.svg" alt="Magnitude comparator" height="70">

- **Python:** `s.magcomp(...)`  ·  **Reference prefix:** `U`
- **Pins:** `A0`, `A1`, `A2`, `A3`, `B0`, `B1`, `B2`, `B3`, `LT`, `EQ`, `GT`

| Setting | Type | Default | |
|---|---|---|---|
| `bits` (Bits) | num | `4` | *shape* port width in bits |
| `cascade` (Cascade inputs) | bool | `False` | *shape*  |
| `bus` (Bus pins) | bool | `False` | *shape* one thick bus pin per port instead of one pin per bit |

**Named variants** (each has its own palette tile and Python method):

| | Variant | Python | Same as |
|---|---|---|---|
| <img src="img/symbols/magnitude_comparator.svg" height="48"> | Magnitude comparator | `s.magnitude_comparator()` | `magcomp` with the defaults |

### Multiplexer

<img src="img/symbols/mux.svg" alt="Multiplexer" height="70">

- **Python:** `s.mux(...)`  ·  **Reference prefix:** `U`
- **Pins:** `I0`, `I1`, `Y`, `S0`

| Setting | Type | Default | |
|---|---|---|---|
| `inputs` (Inputs) | enum: 2, 4, 8, 16 | `2` | *shape*  |
| `width` (Data width) | num | `1` | *shape* bits per input (bus) |
| `enable` (Enable pin) | bool | `False` | *shape*  |

**Named variants** (each has its own palette tile and Python method):

| | Variant | Python | Same as |
|---|---|---|---|
| <img src="img/symbols/mux2.svg" height="48"> | Multiplexer 2:1 | `s.mux2()` | `mux` with the defaults |
| <img src="img/symbols/mux4.svg" height="48"> | Multiplexer 4:1 | `s.mux4()` | `mux` with inputs=4 |
| <img src="img/symbols/mux8.svg" height="48"> | Multiplexer 8:1 | `s.mux8()` | `mux` with inputs=8 |
| <img src="img/symbols/mux16.svg" height="48"> | Multiplexer 16:1 | `s.mux16()` | `mux` with inputs=16 |

### Priority encoder

<img src="img/symbols/encoder.svg" alt="Priority encoder" height="70">

- **Python:** `s.encoder(...)`  ·  **Reference prefix:** `U`
- **Pins:** `I0`, `I1`, `I2`, `I3`, `I4`, `I5`, `I6`, `I7`, `EI`, `A0`, `A1`, `A2`, `GS`, `EO`

| Setting | Type | Default | |
|---|---|---|---|
| `outputs` (Output bits) | num | `3` | *shape* 1 to 5: 2, 4, 8, 16 or 32 inputs |
| `active_low` (Active-low) | bool | `True` | *shape*  |
| `enable` (Enable in / out) | bool | `True` | *shape*  |
| `bus` (Bus pins) | bool | `False` | *shape* one thick bus pin per port instead of one pin per bit |

**Named variants** (each has its own palette tile and Python method):

| | Variant | Python | Same as |
|---|---|---|---|
| <img src="img/symbols/priority_encoder.svg" height="48"> | Priority encoder 8:3 | `s.priority_encoder()` | `encoder` with the defaults |

### Register / latch array

<img src="img/symbols/register.svg" alt="Register / latch array" height="70">

- **Python:** `s.register(...)`  ·  **Reference prefix:** `U`
- **Pins:** `D0`, `D1`, `D2`, `D3`, `D4`, `D5`, `D6`, `D7`, `CLK`, `OE`, `Q0`, `Q1`, `Q2`, `Q3`, `Q4`, `Q5`, `Q6`, `Q7`

| Setting | Type | Default | |
|---|---|---|---|
| `bits` (Bits) | num | `8` | *shape* port width in bits |
| `kind` (Kind) | enum: flip-flop, latch | `flip-flop` | *shape*  |
| `bus` (Bus pins) | bool | `False` | *shape* one thick bus pin per port instead of one pin per bit |
| `oe` (Output enable) | bool | `True` | *shape*  |
| `clear` (Clear) | bool | `False` | *shape*  |

**Named variants** (each has its own palette tile and Python method):

| | Variant | Python | Same as |
|---|---|---|---|
| <img src="img/symbols/register8.svg" height="48"> | Register (D flip-flops) | `s.register8()` | `register` with the defaults |
| <img src="img/symbols/latch8.svg" height="48"> | Transparent latch | `s.latch8()` | `register` with kind='latch' |

### Shift register

<img src="img/symbols/shiftreg.svg" alt="Shift register" height="70">

- **Python:** `s.shiftreg(...)`  ·  **Reference prefix:** `U`
- **Pins:** `SER`, `CLK`, `CLR`, `Q0`, `Q1`, `Q2`, `Q3`, `Q4`, `Q5`, `Q6`, `Q7`, `QS`

| Setting | Type | Default | |
|---|---|---|---|
| `bits` (Bits) | num | `8` | *shape* port width in bits |
| `mode` (Mode) | enum: sipo, piso, siso, pipo | `sipo` | *shape* serial / parallel in, serial / parallel out |
| `bus` (Bus pins) | bool | `False` | *shape* one thick bus pin per port instead of one pin per bit |
| `clear` (Clear) | bool | `True` | *shape*  |
| `oe` (Output enable) | bool | `False` | *shape*  |

**Named variants** (each has its own palette tile and Python method):

| | Variant | Python | Same as |
|---|---|---|---|
| <img src="img/symbols/shiftreg_sipo.svg" height="48"> | Shift register, serial in / parallel out | `s.shiftreg_sipo()` | `shiftreg` with the defaults |
| <img src="img/symbols/shiftreg_piso.svg" height="48"> | Shift register, parallel in / serial out | `s.shiftreg_piso()` | `shiftreg` with mode='piso' |
| <img src="img/symbols/shiftreg_universal.svg" height="48"> | Shift register, universal | `s.shiftreg_universal()` | `shiftreg` with mode='pipo', bits=4 |

## Sources

### Battery / cell

<img src="img/symbols/battery.svg" alt="Battery / cell" height="70">

- **Python:** `s.battery(...)`  ·  **Reference prefix:** `BT`  ·  **SPICE:** `V {p} {n} {src}`
- **Pins:** `p`, `n`
- **Suggested fields:** Capacity, Chemistry, Internal resistance

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `40` | *shape* pin-to-pin distance |
| `cells` (Cells) | enum: 1, 2, 3, 4 | `1` | *shape*  |

### Current sink

<img src="img/symbols/isink.svg" alt="Current sink" height="70">

- **Python:** `s.isink(...)`  ·  **Reference prefix:** `I`  ·  **SPICE:** `I {in} {out} {src}`
- **Pins:** `in`, `out`
- drawn vertically: current flows in at the top and out at the bottom
- **Suggested fields:** Compliance voltage

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `80` | *shape* pin-to-pin distance |

### Current source

<img src="img/symbols/isrc.svg" alt="Current source" height="70">

- **Python:** `s.isrc(...)`  ·  **Reference prefix:** `I`  ·  **SPICE:** `I {p} {n} {src}`
- **Pins:** `p`, `n`
- **Suggested fields:** Compliance voltage

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `100` | *shape* pin-to-pin distance |
| `text` (Text inside) | str | `` | *shape* e.g. e_{n}: drawn in the circle instead of the symbol |

### Current-controlled I source (F)

<img src="img/symbols/cccs.svg" alt="Current-controlled I source (F)" height="70">

- **Python:** `s.cccs(...)`  ·  **Reference prefix:** `F`  ·  **SPICE:** `F {p} {n} {ctrl} {value}`
- **Pins:** `p`, `n`

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `100` | *shape* pin-to-pin distance |
| `control` (Controlling source) | str | `V1` |  name of the voltage source whose current controls this one |

### Current-controlled V source (H)

<img src="img/symbols/ccvs.svg" alt="Current-controlled V source (H)" height="70">

- **Python:** `s.ccvs(...)`  ·  **Reference prefix:** `H`  ·  **SPICE:** `H {p} {n} {ctrl} {value}`
- **Pins:** `p`, `n`

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `100` | *shape* pin-to-pin distance |
| `control` (Controlling source) | str | `V1` |  name of the voltage source whose current controls this one |

### Generator / alternator

<img src="img/symbols/generator.svg" alt="Generator / alternator" height="70">

- **Python:** `s.generator(...)`  ·  **Reference prefix:** `G`
- **Pins:** `1`, `2`

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `100` | *shape* pin-to-pin distance |
| `letter` (Letter) | str | `G` |   |

### Solar cell

<img src="img/symbols/solar.svg" alt="Solar cell" height="70">

- **Python:** `s.solar(...)`  ·  **Reference prefix:** `SC`
- **Pins:** `p`, `n`
- **Suggested fields:** Voc, Isc, Power

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `40` | *shape* pin-to-pin distance |

### Voltage source

<img src="img/symbols/vsrc.svg" alt="Voltage source" height="70">

- **Python:** `s.vsrc(...)`  ·  **Reference prefix:** `V`  ·  **SPICE:** `V {p} {n} {src}`
- **Pins:** `p`, `n`
- **Suggested fields:** Amplitude, Frequency, Offset, Output impedance

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `100` | *shape* pin-to-pin distance |
| `kind` (Kind) | enum: dc, ac, pulse, square, triangle, noise | `dc` | *shape*  |
| `text` (Text inside) | str | `` | *shape* e.g. e_{n}: drawn in the circle instead of the symbol |
| `signs` (Polarity signs) | bool | `True` | *shape*  |

### Voltage-controlled I source (G)

<img src="img/symbols/vccs.svg" alt="Voltage-controlled I source (G)" height="70">

- **Python:** `s.vccs(...)`  ·  **Reference prefix:** `G`  ·  **SPICE:** `G {p} {n} {cp} {cn} {value}`
- **Pins:** `p`, `n`, `cp`, `cn`

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `100` | *shape* pin-to-pin distance |

### Voltage-controlled V source (E)

<img src="img/symbols/vcvs.svg" alt="Voltage-controlled V source (E)" height="70">

- **Python:** `s.vcvs(...)`  ·  **Reference prefix:** `E`  ·  **SPICE:** `E {p} {n} {cp} {cn} {value}`
- **Pins:** `p`, `n`, `cp`, `cn`

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `100` | *shape* pin-to-pin distance |

## Loads & meters

### Buzzer / piezo

<img src="img/symbols/buzzer.svg" alt="Buzzer / piezo" height="70">

- **Python:** `s.buzzer(...)`  ·  **Reference prefix:** `BZ`
- **Pins:** `1`, `2`
- **Suggested fields:** Voltage, Frequency

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `60` | *shape* pin-to-pin distance |

### Electronic load

<img src="img/symbols/load.svg" alt="Electronic load" height="70">

- **Python:** `s.load(...)`  ·  **Reference prefix:** `RL`
- **Pins:** `1`, `2`
- a generic load or DUT drawn as a box
- **Suggested fields:** Mode, Setpoint, Power

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `60` | *shape* pin-to-pin distance |
| `label` (Label) | str | `LOAD` |   |
| `w` (Body length) | num | `40` | *shape* along the leads |
| `h` (Body width) | num | `20` | *shape* across the leads |
| `fill` (Fill) | enum: box, pad | `box` | *shape* box = shaded, pad = white |

### Heater

<img src="img/symbols/heater.svg" alt="Heater" height="70">

- **Python:** `s.heater(...)`  ·  **Reference prefix:** `HE`  ·  **SPICE:** `R {1} {2} {value}`
- **Pins:** `1`, `2`
- **Suggested fields:** Power, Voltage

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `60` | *shape* pin-to-pin distance |

### Lamp

<img src="img/symbols/lamp.svg" alt="Lamp" height="70">

- **Python:** `s.lamp(...)`  ·  **Reference prefix:** `LA`
- **Pins:** `1`, `2`
- **Suggested fields:** Voltage, Power

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `60` | *shape* pin-to-pin distance |

### Loudspeaker

<img src="img/symbols/speaker.svg" alt="Loudspeaker" height="70">

- **Python:** `s.speaker(...)`  ·  **Reference prefix:** `LS`
- **Pins:** `1`, `2`
- **Suggested fields:** Impedance, Power

### Meter (V / A / Ω / W …)

<img src="img/symbols/meter.svg" alt="Meter (V / A / Ω / W …)" height="70">

- **Python:** `s.meter(...)`  ·  **Reference prefix:** `M`
- **Pins:** `1`, `2`
- **Suggested fields:** Range, Accuracy

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `60` | *shape* pin-to-pin distance |
| `letter` (Quantity) | enum: V, A, Ω, W, Hz, mV, mA, µA, G, T, Osc | `V` | *shape*  |

### Microphone

<img src="img/symbols/microphone.svg" alt="Microphone" height="70">

- **Python:** `s.microphone(...)`  ·  **Reference prefix:** `MK`
- **Pins:** `1`, `2`
- **Suggested fields:** Sensitivity, Bias

### Motor

<img src="img/symbols/motor.svg" alt="Motor" height="70">

- **Python:** `s.motor(...)`  ·  **Reference prefix:** `M`
- **Pins:** `1`, `2`
- **Suggested fields:** Voltage, Current, Speed

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `60` | *shape* pin-to-pin distance |
| `kind` (Kind) | enum: dc, ac, stepper | `dc` | *shape*  |

### Test probe / scope tip

<img src="img/symbols/probe.svg" alt="Test probe / scope tip" height="70">

- **Python:** `s.probe(...)`  ·  **Reference prefix:** `TP`
- **Pins:** `p`
- a probe touching a net; one pin

## Electromechanical

### Antenna

<img src="img/symbols/antenna.svg" alt="Antenna" height="70">

- **Python:** `s.antenna(...)`  ·  **Reference prefix:** `AE`
- **Pins:** `p`
- **Suggested fields:** Frequency, Gain, Impedance

| Setting | Type | Default | |
|---|---|---|---|
| `kind` (Kind) | enum: monopole, loop, dipole | `monopole` | *shape*  |

### Connector / header

<img src="img/symbols/connector.svg" alt="Connector / header" height="70">

- **Python:** `s.connector(...)`  ·  **Reference prefix:** `J`
- **Pins:** `1`, `2`, `3`, `4`
- **Suggested fields:** Pitch, Mating part

| Setting | Type | Default | |
|---|---|---|---|
| `pins` (Pins) | num | `4` | *shape*  |
| `gender` (Style) | enum: pin, socket | `pin` | *shape*  |

### Jumper / solder bridge

<img src="img/symbols/jumper.svg" alt="Jumper / solder bridge" height="70">

- **Python:** `s.jumper(...)`  ·  **Reference prefix:** `JP`
- **Pins:** `1`, `2`

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `40` | *shape* pin-to-pin distance |
| `closed` (Closed) | bool | `False` | *shape*  |

### Relay

<img src="img/symbols/relay.svg" alt="Relay" height="70">

- **Python:** `s.relay(...)`  ·  **Reference prefix:** `K`
- **Pins:** `A1`, `A2`, `COM`, `NO`, `NC`
- **Suggested fields:** Coil voltage, Coil resistance, Contact rating

| Setting | Type | Default | |
|---|---|---|---|
| `contact` (Contact) | enum: spst, spdt | `spdt` | *shape*  |
| `latching` (Latching) | bool | `False` | *shape*  |

### Switch / push button

<img src="img/symbols/switch.svg" alt="Switch / push button" height="70">

- **Python:** `s.switch(...)`  ·  **Reference prefix:** `SW`
- **Pins:** `1`, `2`
- **Suggested fields:** Current rating, Voltage rating

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `60` | *shape* pin-to-pin distance |
| `kind` (Kind) | enum: spst, spdt, push_no, push_nc | `spst` | *shape*  |
| `closed` (Closed) | bool | `False` | *shape*  |

## Vacuum tubes

### Pentode

<img src="img/symbols/pentode.svg" alt="Pentode" height="70">

- **Python:** `s.pentode(...)`  ·  **Reference prefix:** `V`
- **Pins:** `P`, `K`, `G1`, `G2`, `G3`
- **Suggested fields:** Heater voltage

| Setting | Type | Default | |
|---|---|---|---|
| `heater` (Heater pins) | bool | `False` | *shape*  |

### Tetrode

<img src="img/symbols/tetrode.svg" alt="Tetrode" height="70">

- **Python:** `s.tetrode(...)`  ·  **Reference prefix:** `V`
- **Pins:** `P`, `K`, `G1`, `G2`
- **Suggested fields:** Heater voltage

| Setting | Type | Default | |
|---|---|---|---|
| `heater` (Heater pins) | bool | `False` | *shape*  |

### Triode

<img src="img/symbols/triode.svg" alt="Triode" height="70">

- **Python:** `s.triode(...)`  ·  **Reference prefix:** `V`
- **Pins:** `P`, `K`, `G`
- **Suggested fields:** Heater voltage, Mu

| Setting | Type | Default | |
|---|---|---|---|
| `heater` (Heater pins) | bool | `False` | *shape*  |

### Vacuum diode

<img src="img/symbols/tube_diode.svg" alt="Vacuum diode" height="70">

- **Python:** `s.tube_diode(...)`  ·  **Reference prefix:** `V`
- **Pins:** `P`, `K`
- **Suggested fields:** Heater voltage

| Setting | Type | Default | |
|---|---|---|---|
| `heater` (Heater pins) | bool | `False` | *shape*  |

## Signal flow

### Amplifier (block)

<img src="img/symbols/amplifier.svg" alt="Amplifier (block)" height="70">

- **Python:** `s.amplifier(...)`  ·  **Reference prefix:** `A`
- **Pins:** `in`, `out`
- **Suggested fields:** Gain, Bandwidth

| Setting | Type | Default | |
|---|---|---|---|
| `gain` (Text inside) | str | `` | *shape* e.g. ×10, G, 20 dB |
| `size` (Size) | num | `40` | *shape*  |

### Attenuator / pad

<img src="img/symbols/attenuator.svg" alt="Attenuator / pad" height="70">

- **Python:** `s.attenuator(...)`  ·  **Reference prefix:** `AT`
- **Pins:** `in`, `out`
- **Suggested fields:** Attenuation, Impedance

### Converter (ADC / DAC / DC-DC)

<img src="img/symbols/converter.svg" alt="Converter (ADC / DAC / DC-DC)" height="70">

- **Python:** `s.converter(...)`  ·  **Reference prefix:** `U`
- **Pins:** `in`, `out`
- **Suggested fields:** Resolution, Sample rate, Efficiency

| Setting | Type | Default | |
|---|---|---|---|
| `src` (From) | str | `A` | *shape*  |
| `dst` (To) | str | `D` | *shape*  |
| `isolated` (Isolated) | bool | `False` | *shape*  |

### Filter (block)

<img src="img/symbols/filter.svg" alt="Filter (block)" height="70">

- **Python:** `s.filter(...)`  ·  **Reference prefix:** `FL`
- **Pins:** `in`, `out`
- **Suggested fields:** Cut-off, Order, Type

| Setting | Type | Default | |
|---|---|---|---|
| `kind` (Response) | enum: lp, hp, bp, bs | `lp` | *shape*  |

### Mixer / multiplier

<img src="img/symbols/mixer.svg" alt="Mixer / multiplier" height="70">

- **Python:** `s.mixer(...)`  ·  **Reference prefix:** `MX`
- **Pins:** `rf`, `lo`, `if`

### Oscillator

<img src="img/symbols/oscillator.svg" alt="Oscillator" height="70">

- **Python:** `s.oscillator(...)`  ·  **Reference prefix:** `X`
- **Pins:** `out`
- **Suggested fields:** Frequency, Stability

### Summing junction

<img src="img/symbols/summer.svg" alt="Summing junction" height="70">

- **Python:** `s.summer(...)`  ·  **Reference prefix:** `S`
- **Pins:** `in1`, `in2`, `out`

| Setting | Type | Default | |
|---|---|---|---|
| `signs` (Signs) | str | `++` | *shape* sign of the left and bottom inputs, e.g. +-  |
| `mark` (Mark) | enum: Σ, +, none | `Σ` | *shape*  |

## Generic

### Block

<img src="img/symbols/block.svg" alt="Block" height="70">

- **Python:** `s.block(...)`  ·  **Reference prefix:** `U`  ·  **SPICE:** `X {*} {model}`
- **Pins:** 

| Setting | Type | Default | |
|---|---|---|---|
| `w` (Width) | num | `160` | *shape*  |
| `h` (Height) | num | `70` | *shape*  |
| `title` (Title) | str | `Block` | *shape*  |
| `lines` (Lines) | text | `` | *shape*  |
| `pins` (Pins) | str | `` | *shape* e.g. "IN:l, OUT:r, VDD:t@0.5" |
| `accent` (Accent fill) | bool | `False` | *shape*  |
| `show_pins` (Pin names) | bool | `True` | *shape*  |

### IC (DIP-style)

<img src="img/symbols/ic.svg" alt="IC (DIP-style)" height="70">

- **Python:** `s.ic(...)`  ·  **Reference prefix:** `U`  ·  **SPICE:** `X {*} {model}`
- **Pins:** `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`
- pins numbered anticlockwise from top left, like a DIP package

| Setting | Type | Default | |
|---|---|---|---|
| `pins` (Pins) | num | `8` | *shape*  |
| `title` (Title) | str | `IC` | *shape*  |
| `names` (Pin names) | str | `` | *shape* comma list in pin order, e.g. "VCC, IN, OUT, GND" |

### Impedance (generic Z)

<img src="img/symbols/impedance.svg" alt="Impedance (generic Z)" height="70">

- **Python:** `s.impedance(...)`  ·  **Reference prefix:** `Z`
- **Pins:** `1`, `2`

| Setting | Type | Default | |
|---|---|---|---|
| `length` (Length) | num | `60` | *shape* pin-to-pin distance |
| `label` (Text inside) | str | `Z` | *shape*  |
| `w` (Body length) | num | `32` | *shape* along the leads |
| `h` (Body width) | num | `16` | *shape* across the leads |
| `fill` (Fill) | enum: box, pad | `box` | *shape* box = shaded, pad = white |

### Norton equivalent

<img src="img/symbols/norton.svg" alt="Norton equivalent" height="70">

- **Python:** `s.norton(...)`  ·  **Reference prefix:** `NO`
- **Pins:** `a`, `b`
- value: the short-circuit current

| Setting | Type | Default | |
|---|---|---|---|
| `zn` (Impedance text) | str | `Zn` | *shape*  |

### Thévenin equivalent

<img src="img/symbols/thevenin.svg" alt="Thévenin equivalent" height="70">

- **Python:** `s.thevenin(...)`  ·  **Reference prefix:** `TH`
- **Pins:** `a`, `b`
- value: the open-circuit voltage

| Setting | Type | Default | |
|---|---|---|---|
| `zth` (Impedance text) | str | `Zth` | *shape*  |

### Two-port network

<img src="img/symbols/twoport.svg" alt="Two-port network" height="70">

- **Python:** `s.twoport(...)`  ·  **Reference prefix:** `N`  ·  **SPICE:** `X {1} {1n} {2} {2n} {model}`
- **Pins:** `1`, `1n`, `2`, `2n`

| Setting | Type | Default | |
|---|---|---|---|
| `title` (Text inside) | str | `N` | *shape*  |
| `w` (Width) | num | `60` | *shape*  |

## Nets

### Bus entry

<img src="img/symbols/busentry.svg" alt="Bus entry" height="70">

- **Python:** `s.busentry(...)`  ·  **Reference prefix:** `—`
- **Pins:** `bus`, `bit`
- the 45° tap from a bus wire to a signal wire; label the bus D[7:0] and the signal D3

| Setting | Type | Default | |
|---|---|---|---|
| `direction` (Direction) | enum: up, down | `up` | *shape*  |

### Ground

<img src="img/symbols/ground.svg" alt="Ground" height="70">

- **Python:** `s.ground(...)`  ·  **Reference prefix:** `—`
- **Pins:** `g`

| Setting | Type | Default | |
|---|---|---|---|
| `kind` (Kind) | enum: earth, signal, chassis | `earth` | *shape*  |
| `net` (Net) | str | `0` |   |

### Junction

<img src="img/symbols/dot.svg" alt="Junction" height="70">

- **Python:** `s.dot(...)`  ·  **Reference prefix:** `—`
- **Pins:** `p`

### Net label

<img src="img/symbols/flag.svg" alt="Net label" height="70">

- **Python:** `s.flag(...)`  ·  **Reference prefix:** `—`
- **Pins:** `p`

| Setting | Type | Default | |
|---|---|---|---|
| `label` (Net name) | str | `NET` | *shape*  |
| `side` (Side) | enum: left, right | `left` | *shape*  |
| `min_width` (Minimum width) | num | `0` | *shape* give several labels the same width, e.g. 60 |

### No-connect mark

<img src="img/symbols/noconnect.svg" alt="No-connect mark" height="70">

- **Python:** `s.noconnect(...)`  ·  **Reference prefix:** `—`
- **Pins:** `p`
- marks a pin as deliberately unconnected

### Supply rail

<img src="img/symbols/rail.svg" alt="Supply rail" height="70">

- **Python:** `s.rail(...)`  ·  **Reference prefix:** `—`
- **Pins:** `p`

| Setting | Type | Default | |
|---|---|---|---|
| `net` (Net) | str | `+5 V` |   |
| `kind` (Kind) | enum: bar, arrow | `bar` | *shape*  |

### Terminal / port

<img src="img/symbols/terminal.svg" alt="Terminal / port" height="70">

- **Python:** `s.terminal(...)`  ·  **Reference prefix:** `J`
- **Pins:** `p`

| Setting | Type | Default | |
|---|---|---|---|
| `label` (Label) | str | `IN` |   |
| `net` (Net) | str | `` |   |

### Test point

<img src="img/symbols/testpoint.svg" alt="Test point" height="70">

- **Python:** `s.testpoint(...)`  ·  **Reference prefix:** `TP`
- **Pins:** `p`

| Setting | Type | Default | |
|---|---|---|---|
| `kind` (Kind) | enum: loop, pad | `loop` | *shape*  |

