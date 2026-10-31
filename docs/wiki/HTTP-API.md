# HTTP API

The editor talks to the server over a small JSON API; other programs can use it too. Interactive documentation is at
`/api/docs` on any running server. If the server has a token, send `Authorization: Bearer <token>` (or open
`/?token=…` once in a browser, which sets a cookie).

Documents are sent as `{"doc": {...}}` ([Document format](Document-Format.md)).

## Information

| | |
|---|---|
| `GET /api/health` | `{"ok": true}` (never needs the token) |
| `GET /api/info` | version, `pdf` (cairosvg available), `scripts`, `public`, workspace, themes and their CSS, text classes, netlist formats, frame sizes |

## Symbols

| | |
|---|---|
| `GET /api/symbols` | the catalogue: every symbol with its settings, default geometry, variants (`presets`), suggested fields, custom definition |
| `POST /api/geometry` | `{"items": [{"sym": "gate", "props": {"inputs": 4}}]}` → the geometry for those settings |
| `PUT /api/symbols/custom/{name}` | save a [custom symbol](Custom-Symbols.md) definition to the workspace library |
| `DELETE /api/symbols/custom/{name}` | remove one |
| `GET /api/symbols/copy/{name}?props={...}` | a custom-symbol definition copied from a built-in symbol |
| `POST /api/symbols/embedded` | `{"symbols": {...}}` register a document's embedded symbols for this session |

## Drawing output

| | |
|---|---|
| `POST /api/export` | `{"doc", "format": "svg\|png\|jpeg\|webp\|pdf\|eps\|tikz\|tikz-standalone", "ids": [...], "background": true\|false\|"#fff", "scale": 2, "margin": 20, "fonts": true, "name": "file"}` → the file |
| `POST /api/render?format=svg\|png\|pdf\|spice&fonts=&scale=` | older single-format endpoint |
| `POST /api/frame` | `{"size": "A4", "orientation": "landscape", "fields": {...}}` → page-frame elements and page size |

```bash
curl -X POST localhost:8000/api/export -H 'content-type: application/json' \
     -d "{\"doc\": $(cat amp.json), \"format\": \"pdf\"}" -o amp.pdf
```

## Netlists

| | |
|---|---|
| `POST /api/netlist` | `{"doc"}` → `{"nets", "warnings", "spice", "pins"}` (the Netlist pane) |
| `POST /api/netlist/export?format=spice\|kicad\|json` | `{"doc"}` → the netlist file |
| `POST /api/netlist/import` | `{"text", "filename"?, "format"?, "title"?}` → `{"doc", "format", "warnings"}` |

## Scripts

| | |
|---|---|
| `POST /api/run` | `{"code", "filename"?}` → `{"ok", "docs": [{"name", "doc"}], "stdout", "error", "traceback"}` |
| `POST /api/import-legacy` | the same for an old `S`-class figure script |

Both answer `403` when scripts are disabled (`SCHEMATRIX_SCRIPTS=0` or a public server).

## Workspace files

| | |
|---|---|
| `GET /api/files` | `[{"path", "size", "modified"}]` (`.json .py .svg .cir .sp .net .tikz .tex`) |
| `GET /api/files/{path}` | the file |
| `PUT /api/files/{path}` | write it (the body is the content; `.json` must be a valid document) |
| `DELETE /api/files/{path}` | delete it |

Paths are relative to the workspace and cannot leave it. On a public server only the bundled examples are listed and
readable, and writing or deleting is refused.

## Errors and limits

Errors come back as `{"detail": "…"}` with 400 (bad input), 401 (token), 403 (disabled), 404, 413 (too large),
429 (rate limit; see `Retry-After`), 501 (an optional dependency is missing) or 503 (busy). Public servers apply the
limits described in [Deployment](Deployment.md#public-server).
