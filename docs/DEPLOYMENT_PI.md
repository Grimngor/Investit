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
TRUSTED_PROXY_AUTH_ENABLED=false
TRUSTED_PROXY_AUTH_ALLOWED_EMAILS=
TRUSTED_PROXY_AUTH_HEADER_EMAIL=Tailscale-User-Login
TRUSTED_PROXY_AUTH_HEADER_NAME=Tailscale-User-Name
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

Use Serve, not Funnel. Serve is private to the tailnet; Funnel is public internet exposure. Tailscale Serve also terminates HTTPS for the app's tailnet URL.

```bash
sudo tailscale up
sudo tailscale serve --bg localhost:${INVESTIT_WEB_PORT:-8080}
sudo tailscale serve status
```

The app is reachable at the Pi's tailnet HTTPS name, such as:

```text
https://raspberrypi.example-tailnet.ts.net
```

Use that `https://...ts.net` URL from trusted devices. Direct local URLs such as `http://127.0.0.1:8080` are intentionally plain HTTP because they are only the localhost hop between Tailscale Serve and the Docker web proxy; browsers will label those direct HTTP URLs as not secure. Do not publish that HTTP port to the LAN or internet to avoid bypassing Tailscale's HTTPS and access controls.

### URL Customization

You can customize the URL without changing InvestIt's Docker or backend configuration:

- Rename the Pi in Tailscale admin or with `sudo tailscale set --hostname=investit-pi` to change the machine-name part of the tailnet URL.
- Enable or rename MagicDNS in Tailscale admin to control the tailnet DNS suffix shown in `tailscale serve status`.
- Use a private custom domain through Tailscale DNS/HTTPS features if you already control the domain. Keep it tailnet-only and point it at the same Serve target, `localhost:${INVESTIT_WEB_PORT:-8080}`.

After any URL change, run:

```bash
sudo tailscale serve status
curl -fsS http://127.0.0.1:${INVESTIT_WEB_PORT:-8080}/health
```

Recommended hardening:

- Confirm `docker compose ps` shows only the `web` service publishing a localhost-bound port.
- Confirm `tailscale serve status` shows Serve, not Funnel.
- Add Tailscale grants for the users/devices that may reach the Pi.
- Keep app registration limited to trusted users because InvestIt still uses app-side login for MVP.
- Keep the Compose web proxy bound to `127.0.0.1`; trusted identity headers must not be accepted on a LAN-bound service.

Reference docs:

- [Tailscale Serve](https://tailscale.com/docs/features/tailscale-serve)
- [tailscale serve command](https://tailscale.com/kb/1242/tailscale-serve)
- [Tailscale grants](https://tailscale.com/docs/features/access-control/grants)

## Pi 5 Validation

After building and starting the stack on the Pi, run the deployment smoke script:

```bash
bash scripts/deploy/validate_pi_deployment.sh
```

Expected result:

- Host architecture is `aarch64` or `arm64`.
- `docker compose config --quiet` passes.
- `docker compose build` and `docker compose up -d` complete.
- `curl -fsS http://127.0.0.1:${INVESTIT_WEB_PORT:-8080}/health` returns successfully.
- `web` publishes `127.0.0.1:${INVESTIT_WEB_PORT:-8080}:80`.
- `backend` has no published host port.
- `tailscale serve status` shows the localhost service, not Funnel.
- `docker stats --no-stream` shows resource usage for the Compose containers.

Record hardware validation notes here after running on the Pi:

| Date | Pi OS / Kernel | Architecture | Docker / Compose | Build time | Runtime notes | Result |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-05-16 | Debian GNU/Linux 13 trixie / Linux 6.12.62+rpt-rpi-2712 | aarch64 | Docker 29.4.3 / Compose v5.1.3 | 2.3s cached image rebuild | Web proxy published only on `127.0.0.1:8080`; backend internal only; `/health` returned healthy; Tailscale Serve exposed the Pi's private `https://<machine>.<tailnet>.ts.net` URL; logs showed normal nginx and Uvicorn startup | Passed without warnings |

Known ARM64 notes:

- The Dockerfiles use Python and Node base images that publish ARM64 variants.
- Backend wheels should install from `requirements.txt` without local compilation on current Raspberry Pi OS 64-bit. If a package compiles locally, record it in the table above.
- Keep `INVESTIT_DATA_DIR` on persistent storage with enough free space for SQLite and backup files.

## Tailscale Passwordless Login

InvestIt can optionally use Tailscale Serve identity headers as a passwordless login source while keeping the normal username/password flow enabled. When `TRUSTED_PROXY_AUTH_ALLOWED_EMAILS` is populated, the same email allowlist is also enforced for registration and password login.

Requirements:

- Use Tailscale Serve, not Funnel.
- Keep the web proxy bound to `127.0.0.1`.
- Registration must use an email listed in `TRUSTED_PROXY_AUTH_ALLOWED_EMAILS`.
- Password login is accepted only for users whose `email` or `username` is listed in `TRUSTED_PROXY_AUTH_ALLOWED_EMAILS`.
- The Tailscale login email must match an existing InvestIt user's `email` or `username`.
- The Tailscale login email must also be listed in `TRUSTED_PROXY_AUTH_ALLOWED_EMAILS`.

Enable it in `.env`:

```env
TRUSTED_PROXY_AUTH_ENABLED=true
TRUSTED_PROXY_AUTH_ALLOWED_EMAILS=you@example.com,friend@example.com
TRUSTED_PROXY_AUTH_HEADER_EMAIL=Tailscale-User-Login
TRUSTED_PROXY_AUTH_HEADER_NAME=Tailscale-User-Name
```

Then rebuild and restart:

```bash
docker compose build
docker compose up -d
```

The login screen will show both password login and `Continue with Tailscale`. If Tailscale login fails, the password login remains available.

## Upgrade And Rollback

For normal updates from the Pi, use the deployment helper:

```bash
cd ~/services/investit
bash scripts/deploy/update_pi.sh
```

The helper checks required tools, refuses to deploy over tracked local changes, creates a pre-deploy SQLite backup under `data/backups/`, runs `git pull --ff-only`, rebuilds the Compose images, restarts the stack, checks `/health`, and prints recent logs.

Useful options:

```bash
bash scripts/deploy/update_pi.sh --pull-images
bash scripts/deploy/update_pi.sh --skip-pull
bash scripts/deploy/update_pi.sh --skip-backup
```

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

## Editing And Moving User Data

Prefer app workflows for portfolio data:

- Use the Portfolio and Orders screens to edit orders, imports, prices, and holdings-derived state.
- Use SQLite only for inspection or maintenance operations that the UI does not expose yet.
- Always create a backup before changing `data/investit.sqlite3`.

For a cold local backup on Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force data\backups
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item data\investit.sqlite3 "data\backups\investit_backup_$stamp.sqlite3"
```

For profile/auth fields that are not editable in the UI, use the app persistence layer from the repository root after backing up:

```powershell
.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'backend'); from app.models.persistence import load_user_data, save_user_data; u = load_user_data('<username>'); u['full_name'] = 'Your Name'; u['email'] = 'you@example.com'; save_user_data('<username>', u)"
```

Do not hand-edit password hashes unless you know the expected hash format. To change a password, prefer adding a dedicated maintenance command before doing it on real data.

To copy your local primary-user data to the Pi, transfer the SQLite database as a stopped-service restore:

```bash
cd ~/services/investit
docker compose down
mkdir -p data/backups
cp data/investit.sqlite3 data/backups/investit_pi_before_restore_$(date -u +%Y%m%d_%H%M%S).sqlite3
```

From Windows PowerShell, copy the local database:

```powershell
scp data\investit.sqlite3 <pi-user>@<pi-host>:~/services/investit/data/investit.sqlite3
```

Then restart and verify on the Pi:

```bash
cd ~/services/investit
rm -f data/investit.sqlite3-wal data/investit.sqlite3-shm
docker compose up -d
curl -fsS http://127.0.0.1:${INVESTIT_WEB_PORT:-8080}/health
```

Copy the main `.sqlite3` file while the app is stopped. The `-wal` and `-shm` files are SQLite runtime files and should not be copied as the source of truth for a stopped-service restore.

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
