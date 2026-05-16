#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

warn_count=0

log() {
	printf '\n==> %s\n' "$1"
}

pass() {
	printf '[OK] %s\n' "$1"
}

warn() {
	warn_count=$((warn_count + 1))
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

published_ports_for_service() {
	local service_name="$1"
	docker compose ps --format json "$service_name" \
		| python3 -c 'import json, sys
ports = []
for line in sys.stdin:
	line = line.strip()
	if not line:
		continue
	item = json.loads(line)
	value = item.get("Publishers") or item.get("Ports") or []
	if isinstance(value, list):
		for port in value:
			if isinstance(port, dict):
				url = port.get("URL") or ""
				published = port.get("PublishedPort")
				target = port.get("TargetPort")
				protocol = port.get("Protocol") or "tcp"
				if published:
					ports.append(f"{url}:{published}->{target}/{protocol}".lstrip(":"))
			elif port:
				ports.append(str(port))
	elif value:
		ports.append(str(value))
print("\n".join(ports))'
}

log "Host"
[[ -f compose.yaml ]] || fail "Run this script from the InvestIt repository root or keep its relative path intact."
arch="$(uname -m)"
os_release="$(. /etc/os-release && printf '%s %s' "${PRETTY_NAME:-Linux}" "${VERSION_CODENAME:-}")"
printf 'OS: %s\n' "$os_release"
printf 'Architecture: %s\n' "$arch"
case "$arch" in
	aarch64 | arm64) pass "ARM64 architecture detected" ;;
	*) warn "Expected Raspberry Pi 5 ARM64/aarch64, got ${arch}" ;;
esac

log "Tooling"
require_command docker
require_command curl
require_command python3
docker --version
docker compose version
pass "Docker and Compose are available"

log "Environment"
[[ -f .env ]] || fail ".env is missing. Copy .env.example to .env and set deployment values first."
web_port="$(read_env_value INVESTIT_WEB_PORT 8080)"
data_dir="$(read_env_value INVESTIT_DATA_DIR ./data)"
[[ -n "$(read_env_value SECRET_KEY "")" ]] || fail "SECRET_KEY is empty"
if [[ "$(read_env_value SECRET_KEY "")" == "change-me" ]]; then
	warn "SECRET_KEY still uses the example value"
fi
[[ "$(read_env_value PERSISTENCE_BACKEND sqlite)" == "sqlite" ]] || warn "PERSISTENCE_BACKEND is not sqlite"
printf 'INVESTIT_WEB_PORT=%s\n' "$web_port"
printf 'INVESTIT_DATA_DIR=%s\n' "$data_dir"
pass "Environment file is present"

log "Compose configuration"
docker compose config --quiet
pass "docker compose config is valid"

log "Build and start"
docker compose build
docker compose up -d
docker compose ps
pass "Compose stack is running"

log "Health"
health_url="http://127.0.0.1:${web_port}/health"
curl -fsS "$health_url"
printf '\n'
pass "Health endpoint responded at ${health_url}"

log "Port exposure"
web_port_mapping="$(docker compose port web 80 || true)"
backend_published_ports="$(published_ports_for_service backend)"
printf 'web: %s\n' "${web_port_mapping:-not published}"
printf 'backend: %s\n' "${backend_published_ports:-not published}"
if [[ "$web_port_mapping" != 127.0.0.1:* ]]; then
	fail "web service must publish only on 127.0.0.1, got: ${web_port_mapping:-none}"
fi
if [[ -n "$backend_published_ports" ]]; then
	fail "backend service must not publish a host port, got: ${backend_published_ports}"
fi
pass "Only the web proxy is published, and it is localhost-bound"

log "Tailscale"
if command -v tailscale >/dev/null 2>&1; then
	tailscale status --self || warn "tailscale status --self failed"
	tailscale serve status || warn "tailscale serve status failed. Configure Serve with: sudo tailscale serve --bg localhost:${web_port}"
else
	warn "tailscale command not found"
fi

log "Container resource snapshot"
container_ids="$(docker compose ps -q)"
if [[ -n "$container_ids" ]]; then
	docker stats --no-stream $container_ids || warn "docker stats failed"
else
	warn "No Compose containers found for docker stats"
fi

log "Recent logs"
docker compose logs --tail 50 backend web

log "Result"
if [[ "$warn_count" -gt 0 ]]; then
	warn "Validation completed with ${warn_count} warning(s)"
else
	pass "Validation completed without warnings"
fi
