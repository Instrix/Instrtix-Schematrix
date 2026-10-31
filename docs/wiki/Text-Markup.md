# Text markup

Every text in Schematrix (references, values, part numbers, fields, net labels, notes, block titles, title blocks)
understands a small markup language, close to KiCad's. Press **F1** anywhere in the editor for the reference window:
it shows each construct rendered, has a live preview, and clicking a row inserts it into the field you were editing
(wrapping the selected text, so select `RST` and click *Negation* to get `~{RST}`).

![Text markup reference](img/markup.png)

## Formatting

| Type | Get | Notes |
|---|---|---|
| `~{RST}` | R̅S̅T̅ (overbar) | active-low / negation |
| `V_{CC}` | V<sub>CC</sub> | subscript |
| `x^{2}` | x<sup>2</sup> | superscript |
| `~{CS_{1}}` | nested | markers nest |

Markers only count when a brace follows: `f_c`, `a^b` and `~5` stay as typed.

## Symbols

| Type | Get | | Type | Get |
|---|---|---|---|---|
| `\ohm`, `\Omega` | Ω | | `\le` `\ge` `\ne` `\approx` | ≤ ≥ ≠ ≈ |
| `\u`, `\mu`, `\micro` | µ | | `\inf`, `\infty` | ∞ |
| `\deg`, `\degree` | ° | | `\sqrt` | √ |
| `\pm` | ± | | `\to` `\larrow` `\uarrow` `\darrow` | → ← ↑ ↓ |
| `\times` `\cdot` `\div` | × · ÷ | | `\parallel` `\angle` `\propto` `\partial` | ∥ ∠ ∝ ∂ |
| `\-` | − (true minus) | | `\sum` `\prod` `\int` | Σ Π ∫ |
| `\permil` | ‰ | | `\Re` `\Im` `\hbar` `\bullet` `\dots` | ℜ ℑ ℏ • … |

Greek letters by name: `\alpha \beta \gamma \delta \epsilon \zeta \eta \theta \iota \kappa \lambda \mu \nu \xi \pi
\rho \sigma \tau \upsilon \phi \chi \psi \omega`, and capitals `\Gamma \Delta \Theta \Lambda \Xi \Pi \Sigma \Phi \Psi
\Omega`.

Names are matched longest-first, so `\uF` gives µF and `\ohm` gives Ω. To put a letter right after a name, end the
name with `{}`: `25 \deg{}C` → 25 °C. Unknown names stay as typed (`\foo`).

## Literal characters

| Type | Get |
|---|---|
| `\~` `\_` `\^` | ~ _ ^ (when followed by `{`) |
| `\{` `\}` | { } |
| `\\` | \ |
| `\$` | $ |

## Examples

| Type | Get |
|---|---|
| `4.7 k\ohm \pm1 %` | 4.7 kΩ ±1 % |
| `10 \uF / 25 V` | 10 µF / 25 V |
| `R_{DS(on)} \le 21 m\ohm` | R<sub>DS(on)</sub> ≤ 21 mΩ |
| `~{OE}`, `~{CS_{1}}` | O̅E̅, C̅S̅₁ |
| `f_{c} = 1 / (2\pi RC)` | f<sub>c</sub> = 1 / (2πRC) |
| `I_{OUT} = 5 mA, T_{j} \le 150 \deg{}C` | I<sub>OUT</sub> = 5 mA, T<sub>j</sub> ≤ 150 °C |

## How it comes out

- **Editor, SVG, PNG, JPEG, WebP**: overbars and sub/superscripts as typeset text.
- **PDF, EPS, server PNG**: the same; overbars are drawn as lines measured with the output font.
- **TikZ / LaTeX**: `\overline{}`, `\textsubscript{}`, `\textsuperscript{}` and math-mode symbols (`$\Omega$`).
- **Netlists**: the plain visible text: `10 k\ohm` → SPICE value `10k`; net `V_{OUT}` → node `VOUT`.
- **Text widths** (symbol layout, block sizes) count visible characters only.
