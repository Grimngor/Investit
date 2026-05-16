#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

skip_pull=false
skip_backup=false
build_pull=false

usage() {
	cat <<'EOF'
Usage: bash scripts/deploy/update_pi.sh [options]

Pull, build, and deploy InvestIt on the Raspberry Pi.

Options:
  --skip-pull      Do not run git pull.
  --skip-backup    Do not create a pre-deploy SQLite backup.
  --pull-images    Pass --pull to docker compose build.
  -h, --help       Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
	case "$1" in
		--skip-pull)
			skip_pull=true
			;;
		--skip-backup)
			skip_backup=true
			;;
		--pull-images)
			build_pull=true
			;;
		-h | --help)
			usage
			exit 0
			;;
		*)
			printf 'Unknown option: %s\n\n' "$1" >&2
			usage >&2
			exit 2
			;;
	esac
	shift
done

log() {
	printf '\n==> %s\n' "$1"
}

pass() {
	printf '[OK] %s\n' "$1"
}

warn() {
	printf '[WARN] %s\n' "$1"
}

fail() {
	printf '[FAIL] %s\n' "$1" >&2
	exit 1
}

read_env_value() {
	local key="$1"
	local fallback="$2"

	if [[ ! -f .env ]]; then
		printf '%s' "$fallback"
		return
	fi

	local value
	value="$(grep -E "^${key}=" .env | tail -n 1 | cut -d '=' -f 2- || true)"
	value="${value%\"}"
	value="${value#\"}"
	printf '%s' "${value:-$fallback}"
}

require_command() {
	local command_name="$1"
	command -v "$command_name" >/dev/null 2>&1 || fail "Missing required command: ${command_name}"
}

is_service_running() {
	local service_name="$1"
	local container_id
	container_id="$(docker compose ps -q "$service_name" 2>/dev/null || true)"
	[[ -n "$container_id" ]] && docker inspect -f '{{.State.Running}}' "$container_id" 2>/dev/null | grep -qx true
}

backup_sqlite() {
	local data_dir="$1"
	local db_path="${data_dir%/}/investit.sqlite3"
	local backup_dir="${data_dir%/}/backups"
	local stamp
	stamp="$(date -u +%Y%m%d_%H%M%S)"

	mkdir -p "$backup_dir"

	if is_service_running backend; then
		log "Database backup"
		docker compose exec -T backend python - <<'PY'
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

source = Path("/app/data/investit.sqlite3")
target_dir = Path("/app/data/backups")
target_dir.mkdir(parents=True, exist_ok=True)
target = target_dir / f"investit_pre_deploy_{datetime.now(UTC):%Y%m%d_%H%M%S}.sqlite3"

with sqlite3.connect(source) as src, sqlite3.connect(target) as dst:
	src.backup(dst)

print(target)
PY
		pass "Created online SQLite backup through backend container"
		return
	fi

	if [[ -f "$db_path" ]]; then
		log "Database backup"
		cp "$db_path" "${backup_dir}/investit_pre_deploy_${stamp}.sqlite3"
		pass "Created cold SQLite backup at ${backup_dir}/investit_pre_deploy_${stamp}.sqlite3"
	else
		warn "No SQLite database found at ${db_path}; skipping backup"
	fi
}

wait_for_health() {
	local url="$1"
	local attempts=30
	local delay_seconds=2

	for attempt in $(seq 1 "$attempts"); do
		if curl -fsS "$url" >/dev/null; then
			pass "Health endpoint responded at ${url}"
			return
		fi
		printf 'Waiting for health endpoint (%s/%s)...\n' "$attempt" "$attempts"
		sleep "$delay_seconds"
	done

	fail "Health endpoint did not respond at ${url}"
}

log "Preflight"
[[ -f compose.yaml ]] || fail "Run this script from the InvestIt repository root or keep its relative path intact."
[[ -f .env ]] || fail ".env is missing. Copy .env.example to .env and set deployment values first."
require_command git
require_command docker
require_command curl
require_command python3
docker compose version
pass "Required commands are available"

web_port="$(read_env_value INVESTIT_WEB_PORT 8080)"
data_dir="$(read_env_value INVESTIT_DATA_DIR ./data)"
health_url="http://127.0.0.1:${web_port}/health"

if [[ "$(read_env_value SECRET_KEY "")" == "change-me" ]]; then
	fail "SECRET_KEY still uses the example value"
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
	fail "Tracked working tree changes are present. Commit, stash, or discard them before deploying on the Pi."
fi

if [[ "$skip_backup" == false ]]; then
	backup_sqlite "$data_dir"
else
	warn "Skipping database backup because --skip-backup was provided"
fi

if [[ "$skip_pull" == false ]]; then
	log "Pull latest code"
	git fetch --prune
	git pull --ff-only
	pass "Repository is up to date"
else
	warn "Skipping git pull because --skip-pull was provided"
fi

log "Compose configuration"
docker compose config --quiet
pass "docker compose config is valid"

log "Build images"
if [[ "$build_pull" == true ]]; then
	docker compose build --pull
else
	docker compose build
fi
pass "Images built"

log "Deploy stack"
docker compose up -d --remove-orphans
docker compose ps
pass "Compose stack started"

log "Health check"
wait_for_health "$health_url"

log "Tailscale Serve"
if command -v tailscale >/dev/null 2>&1; then
	tailscale serve status || warn "Tailscale Serve is not configured or status failed. Expected target: localhost:${web_port}"
else
	warn "tailscale command not found"
fi

log "Recent logs"
docker compose logs --tail 30 backend web

log "Done"
pass "InvestIt update completed"
