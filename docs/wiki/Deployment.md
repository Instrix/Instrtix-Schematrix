# Deployment

Schematrix runs as a web server for a team or the public. Two Docker Compose templates in `deploy/` cover the two
cases:

| | Private server | Public server |
|---|---|---|
| File | `deploy/docker-compose.yml` | `deploy/docker-compose.public.yml` |
| Who | your team | anyone, anonymously |
| Access | a shared token | open |
| Python scripts | yes (switchable) | never |
| Storage | a workspace volume: documents, scripts, custom symbols | none; visitors keep sheets in their browser |
| Custom symbols | yes | no |

Both run the published image hardened: read-only filesystem (only the data volume and scratch space writable), all
Linux capabilities dropped, no privilege escalation, memory / CPU / process limits, rotated logs. Both have an `https`
profile that puts Caddy in front with automatic certificates.

The image is published privately on GitHub's registry: run `docker login ghcr.io` with a GitHub token that has
`read:packages`, or uncomment `build: ..` in the compose file to build from a checkout.

## Private server

```bash
cp deploy/.env.example deploy/.env      # set SCHEMATRIX_TOKEN:  openssl rand -hex 24
docker compose -f deploy/docker-compose.yml up -d
```

Open `http://<host>:8000/?token=<token>` once per browser (it sets a cookie); API clients send
`Authorization: Bearer <token>`. The server refuses to start without a token.

**Why a token**: the editor's Script pane runs Python on the server, so anyone who reaches the port could run code in
the container and read or change every document. The template binds the port to `127.0.0.1` by default; expose it
(`SCHEMATRIX_BIND=0.0.0.0`) or use the `https` profile only with the token set.

**Data**: documents, scripts and custom symbols live in the `schematrix_data` volume (Docker manages it; nothing to
configure). Without a volume they would be lost whenever the container is replaced, for instance on every update.

```bash
# HTTPS on your domain (ports 80 and 443 open, DNS pointing here)
SCHEMATRIX_DOMAIN=schematrix.example.org docker compose -f deploy/docker-compose.yml --profile https up -d
# update
docker compose -f deploy/docker-compose.yml pull && docker compose -f deploy/docker-compose.yml up -d
# back up
docker run --rm -v schematrix_data:/data -v "$PWD":/backup alpine tar czf /backup/schematrix-data.tgz -C /data .
```

`deploy/.env` settings: `SCHEMATRIX_TOKEN` (required), `SCHEMATRIX_IMAGE` / `SCHEMATRIX_VERSION` (image and tag),
`SCHEMATRIX_BIND` / `SCHEMATRIX_PORT`, `SCHEMATRIX_SCRIPTS` (1 / 0), `SCHEMATRIX_SCRIPT_TIMEOUT`, `SCHEMATRIX_MEMORY`,
`SCHEMATRIX_CPUS`, `SCHEMATRIX_DOMAIN`.

## Public server

```bash
docker compose -f deploy/docker-compose.public.yml up -d          # http://<host>:8000, no token, no volume
```

Public mode (`SCHEMATRIX_PUBLIC=1`) is safe because of what the server will not do:

- **no code execution**: scripts and legacy import are off, whatever `SCHEMATRIX_SCRIPTS` says;
- **nothing stored on the server**: File > Save downloads the `.json`, the examples are read-only, custom symbols are
  off, documents carrying custom symbols are refused;
- **bounded work**: per-visitor request rates, request and document size, bitmap export scale and pixels, and the
  number of exports running at once are capped;
- **hardened output**: raw SVG is stripped of scripts, exports are served sandboxed, the page has a strict content
  security policy.

The editor still shows these features: a dismissible banner at the top, a note in the Script pane, and a short message
when someone opens the symbol editor or legacy import, all pointing to the desktop app or a self-hosted server.

| Limit | Default | Variable |
|---|---|---|
| requests per minute per visitor | 240 | `SCHEMATRIX_PUBLIC_RATE` |
| exports / imports per minute per visitor | 30 | `SCHEMATRIX_PUBLIC_HEAVY_RATE` |
| request size | 4 MB | `SCHEMATRIX_PUBLIC_MAX_BODY` |
| elements per document | 4000 | `SCHEMATRIX_PUBLIC_MAX_ELEMENTS` |
| bitmap scale | 4× | `SCHEMATRIX_PUBLIC_MAX_SCALE` |
| bitmap pixels | 40 M | `SCHEMATRIX_PUBLIC_MAX_PIXELS` |
| exports at once (server-wide) | 2 | `SCHEMATRIX_PUBLIC_PARALLEL` |

### Before going public

1. **Image access**: `docker login ghcr.io` on the host (or build from a checkout).
2. **HTTPS**: point a DNS name at the host, open ports 80 and 443, and start with the `https` profile, binding the app to
   localhost and trusting the proxy:
   ```bash
   SCHEMATRIX_DOMAIN=schematrix.example.org SCHEMATRIX_TRUST_PROXY=1 SCHEMATRIX_BIND=127.0.0.1 \
     docker compose -f deploy/docker-compose.public.yml --profile https up -d
   ```
3. **Never trust the proxy header without the proxy**: with `SCHEMATRIX_TRUST_PROXY=1` and the app port reachable
   directly, visitors can fake their address in `X-Forwarded-For` and get around the rate limits.
4. **One container**: the limits are counted inside each container; several containers behind a load balancer multiply
   them (rate-limit at the load balancer instead).
5. **Tune** the limits and `SCHEMATRIX_MEMORY` / `SCHEMATRIX_CPUS` for your hardware and audience.

## Without Docker

```bash
pip install "schematrix[export] @ git+ssh://git@github.com/Instrix/instrtix-schematrix.git"
SCHEMATRIX_TOKEN=… SCHEMATRIX_WORKSPACE=/srv/schematrix schematrix serve --host 0.0.0.0 --port 8000
```

Run it under systemd or a process manager, behind a reverse proxy for HTTPS.

## All server settings

| Variable | Default | |
|---|---|---|
| `SCHEMATRIX_WORKSPACE` | `~/Schematrix` (`/data` in Docker) | documents, scripts, custom symbols |
| `SCHEMATRIX_TOKEN` | unset | require this token on every request |
| `SCHEMATRIX_SCRIPTS` | `1` | allow the editor to run Python on the server |
| `SCHEMATRIX_SCRIPT_TIMEOUT` | `30` | seconds per script |
| `SCHEMATRIX_PUBLIC` | `0` | anonymous public mode (above) |
| `SCHEMATRIX_TRUST_PROXY` | `0` | rate-limit by the address a reverse proxy appends to `X-Forwarded-For` |
| `SCHEMATRIX_HOST`, `SCHEMATRIX_PORT` | `127.0.0.1`, `8000` | for `schematrix serve` |
| `SCHEMATRIX_ENGINE` | `auto` | app window engine (desktop) |
