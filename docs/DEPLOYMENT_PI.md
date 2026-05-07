# Raspberry Pi 5 Deployment

This runbook deploys InvestIt on a 64-bit Raspberry Pi OS or other ARM64 Linux host with Docker Compose. The app remains private to trusted users through Tailscale Serve, while InvestIt keeps its current username/password login and JWT session model.

Do not expose this app with Tailscale Funnel, router port forwarding, or a LAN-bound backend port. InvestIt stores private financial data locally.

## Architecture

```text
trusted device
  -> Tailscale Serve HTTPS URL
  -> localhost-bound Docker web proxy on the Pi
  -> frontend static files, /api proxy, and /ws proxy
  -> FastAPI backend on the internal Compose network
  -> SQLite database in ./data/investit.sqlite3
```

The backend service is not published with `ports`; it is only reachable from the internal Compose network. The `web` service binds to `127.0.0.1:${INVESTIT_WEB_PORT:-8080}:80`, so Tailscale Serve can proxy it without exposing it to the LAN.

## First Install

Install Docker Engine, the Compose plugin, and Tailscale on the Pi. Docker is installed at the operating-system level, not inside the project Python virtual environment.

Official Docker Engine supports Debian 13 and ARM64. Set up Docker's apt repository and install the engine:

```bash
sudo apt update
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/debian
Suites: $(. /etc/os-release && echo "$VERSION_CODENAME")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo docker run hello-world
```

Optional: allow your user to run Docker without `sudo`, then log out and back in:

```bash
sudo usermod -aG docker "$USER"
```

Then place InvestIt under your services directory:

```bash
mkdir -p ~/services
cd ~/services
git clone <repo-url> investit
cd investit
```

If the repository already exists somewhere else on the Pi, move or copy it so the project root is:

```text
~/services/investit
```

```bash
cp .env.example .env
python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
```

Edit `.env`:

```env
SECRET_KEY=<generated-value>
PERSISTENCE_BACKEND=sqlite
DATABASE_PATH=data/investit.sqlite3
INVESTIT_WEB_PORT=8080
INVESTIT_DATA_DIR=./data
FINNHUB_API_KEY=
OPENFIGI_API_KEY=
```

`compose.yaml` overrides the backend container database path to `/app/data/investit.sqlite3`, while the host keeps the database under `INVESTIT_DATA_DIR`, which defaults to `./data/`.

Build and start:

```bash
docker compose build
docker compose up -d
docker compose ps
curl -fsS http://127.0.0.1:${INVESTIT_WEB_PORT:-8080}/health
```

## Tailscale Serve

Use Serve, not Funnel. Serve is private to the tailnet; Funnel is public internet exposure. Tailscale Serve can also add identity headers, but InvestIt does not consume those headers yet.

```bash
sudo tailscale up
sudo tailscale serve --bg localhost:${INVESTIT_WEB_PORT:-8080}
sudo tailscale serve status
```

The app is reachable at the Pi's tailnet HTTPS name, such as:

```text
https://raspberrypi.example-tailnet.ts.net
```

Recommended hardening:

- Confirm `docker compose ps` shows only the `web` service publishing a localhost-bound port.
- Confirm `tailscale serve status` shows Serve, not Funnel.
- Add Tailscale grants for the users/devices that may reach the Pi.
- Keep app registration limited to trusted users because InvestIt still uses app-side login for MVP.

Reference docs:

- [Tailscale Serve](https://tailscale.com/docs/features/tailscale-serve)
- [tailscale serve command](https://tailscale.com/kb/1242/tailscale-serve)
- [Tailscale grants](https://tailscale.com/docs/features/access-control/grants)

## Upgrade And Rollback

Upgrade:

```bash
docker compose down
cp data/investit.sqlite3 data/investit.sqlite3.pre-upgrade
git pull
docker compose build
docker compose up -d
curl -fsS http://127.0.0.1:${INVESTIT_WEB_PORT:-8080}/health
```

Rollback to the previous Git revision:

```bash
docker compose down
git checkout <previous-good-revision>
cp data/investit.sqlite3.pre-upgrade data/investit.sqlite3
docker compose build
docker compose up -d
```

Use `git switch -` or your deployment branch once the rollback is resolved.

## Backup And Restore

Runtime data lives in:

```text
data/investit.sqlite3
data/investit.sqlite3-wal
data/investit.sqlite3-shm
data/backups/
```

For a consistent SQLite backup while the app is running, use SQLite's backup command from the backend container:

```bash
docker compose exec -T backend python - <<'PY'
import sqlite3
from datetime import datetime, UTC
from pathlib import Path

source = Path("/app/data/investit.sqlite3")
target_dir = Path("/app/data/backups")
target_dir.mkdir(parents=True, exist_ok=True)
target = target_dir / f"investit_backup_{datetime.now(UTC):%Y%m%d_%H%M%S}.sqlite3"

with sqlite3.connect(source) as src, sqlite3.connect(target) as dst:
	src.backup(dst)

print(target)
PY
```

Alternative cold backup:

```bash
docker compose down
mkdir -p data/backups
cp data/investit.sqlite3 data/backups/investit_backup_$(date -u +%Y%m%d_%H%M%S).sqlite3
docker compose up -d
```

Restore:

```bash
docker compose down
cp data/backups/<backup-file>.sqlite3 data/investit.sqlite3
docker compose up -d
curl -fsS http://127.0.0.1:${INVESTIT_WEB_PORT:-8080}/health
```

Keep off-device encrypted backups for real portfolio data.

## Release Checks

Before deploying a new version:

```bash
python -m pytest backend/tests -q
python -m ruff check backend
python -m ruff format --check backend

cd frontend
npm run build
npx vitest run
npm run test:e2e
```

Deployment smoke checks:

- `docker compose build`
- `docker compose up -d`
- `curl -fsS http://127.0.0.1:${INVESTIT_WEB_PORT:-8080}/health`
- Log in through the Tailscale URL.
- Confirm dashboard load, CSV import, manual price refresh, and WebSocket updates.
- Confirm the backend service has no published LAN port.
