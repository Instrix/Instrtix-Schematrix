# Exporting

## The Export dialog

**Export > Export…** (`Ctrl E`), or right-click a selection > **Export selection…**.

![Export dialog](img/export-dialog.png)

| Option | |
|---|---|
| **Format** | SVG, PNG, JPEG, WebP, PDF, EPS, TikZ, LaTeX standalone (TikZ) |
| **Area** | *Whole sheet*, or *Selection only*: just the selected items, cropped to them plus the margin |
| **Background** | *Theme paper* (the theme's background colour), *White*, or *Transparent* (not for JPEG) |
| **Scale** (bitmaps) | 1× … 8× = 96 … 768 dpi; 2× (192 dpi) suits screens and slides, 4× (384 dpi) print |
| **Margin** | space around the drawing when the page is sized to it (auto page, or a selection) |
| **Embed fonts** (SVG) | include the fonts in the file (portable, ~200 kB) or not (small; viewers need the fonts) |
| **File name** | |
| **Copy** | for SVG and TikZ: copy the text to the clipboard instead of downloading |

The dialog remembers your last choices; the quick items in the Export menu (SVG, PNG, JPEG, PDF, EPS, TikZ) export
the whole sheet with them. *SVG (plain, like the originals)* is SVG without embedded fonts.

## Which format?

| Format | Kind | Use it for |
|---|---|---|
| **SVG** | vector | web pages, Inkscape / Illustrator, Word and PowerPoint (Insert > Pictures), further editing |
| **PNG** | bitmap, lossless, transparency | slides, chat, documents that don't take vectors |
| **JPEG** | bitmap, no transparency | places that insist on JPEG |
| **WebP** | bitmap, small | web pages |
| **PDF** | vector | printing, LaTeX (`\includegraphics`), sending to others |
| **EPS** | vector (PostScript) | old LaTeX workflows (`latex` + `dvips`), some journals |
| **TikZ** | LaTeX code | LaTeX documents: text set in the document's font, see [LaTeX](LaTeX.md) |
| **LaTeX standalone** | a `.tex` file | compiling the figure on its own to a cropped PDF |
| **Document (.json)** | Schematrix | archiving, sharing, version control |
| **Netlists** | SPICE / KiCad / JSON | see [Netlists](Netlists.md) |

## Page size and cropping

- With **Auto size** on (document inspector), the page is the drawing plus the margin: exports are cropped tightly.
- With a fixed **Size** / **Origin**, exports use that page (handy for a series of figures with identical sizes);
  *Fit page to drawing* sets it from the current drawing.
- A [page frame](Page-Frames.md) sets the page to a paper size.
- **Selection only** always crops to the selection plus the margin, whatever the page.

## How exports are made

- **SVG** and **TikZ** are produced by the server in pure Python; they always work.
- **PNG, JPEG, WebP** from the editor are drawn **in your browser** from the server's SVG, so they work everywhere and
  use exactly the fonts you see.
- **PDF and EPS** (and bitmaps from the CLI / Python / API) use `cairosvg` on the server (the `export` extra). They
  use the fonts installed on the server: install JetBrains Mono and Inter for the default theme
  (`fonts-jetbrains-mono fonts-inter`; the Docker image has them), Times New Roman or Liberation Serif for `formal`.

## From the command line

```bash
schematrix render fig.json -o fig.pdf                         # format from the extension
schematrix render figs.py -o out/ -f svg,pdf,png --scale 3    # every schematic a script makes, several formats
schematrix render fig.json -o fig.png --background none       # transparent
schematrix render fig.json -o fig.svg --fonts                 # SVG with embedded fonts
schematrix render fig.json -o fig.tikz                        # TikZ;  -o fig.tex for a standalone file
```

Formats: `svg png jpg webp pdf eps tikz tex json cir` (SPICE) `net` (KiCad). See [Command line](Command-Line.md).

## From Python

```python
s.export('fig.pdf')                                  # format from the extension
s.export('fig.png', scale=4, background=False)       # transparent, 384 dpi
s.export('amp.svg', ids=[u1.id, r1.id, r2.id], margin=10)   # only some elements, cropped
s.export('fig.svg', fonts=False)                     # SVG without embedded fonts
tikz = s.to_tikz()                                   # TikZ code as a string;  to_tikz(standalone=True)
svg = s.to_svg(embed_fonts=True)
```

`background` is `True` (theme paper), `False` (transparent) or a colour such as `'#ffffff'`.

## Over HTTP

`POST /api/export` with `{"doc": …, "format": "png", "ids": [...], "background": false, "scale": 3, "margin": 10}`
returns the file. See [HTTP API](HTTP-API.md).

## Copy and paste

*Export > Copy SVG to clipboard* puts plain SVG text on the clipboard (paste into Inkscape, a web page, a Markdown
file). Copy / paste of elements (`Ctrl C` / `Ctrl V`) uses the clipboard too, so parts move between sheets and windows.
