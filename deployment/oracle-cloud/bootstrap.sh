#!/usr/bin/env bash
# Bootstrap an Oracle Cloud Always Free VM to run md-bridge behind Caddy.
#
# Usage (run as root, see deployment/oracle-cloud/README.md):
#   sudo MD_BRIDGE_DOMAIN="example.com" ./bootstrap.sh
#
# Environment variables:
#   MD_BRIDGE_DOMAIN   Domain name pointed at this VM. Required.
#   MD_BRIDGE_INSECURE Set to 1 to serve over plain HTTP only (when you do
#                      not have a real domain and only want a proof of life
#                      via the public IP).
#   MD_BRIDGE_IMAGE_TAG  Image tag to pull (default: latest).
#   MD_BRIDGE_REF      Git ref the smoke test script is fetched from and run
#                      as root in insecure mode (default: main). Pin it to the
#                      same tag as the images for a reproducible bootstrap.
#   MD_BRIDGE_API_TOKEN  If set, the conversion routes require a matching
#                      X-API-Key header. Left unset the demo stays open.
#
# Exit codes:
#   0  success
#   1  missing prerequisites
#   2  failed to start the stack

set -euo pipefail

DOMAIN="${MD_BRIDGE_DOMAIN:-}"
INSECURE="${MD_BRIDGE_INSECURE:-0}"
INSTALL_DIR="/opt/md-bridge"
IMAGE_TAG="${MD_BRIDGE_IMAGE_TAG:-latest}"
REF="${MD_BRIDGE_REF:-main}"
# Public-deploy defenses. Overridable via the same env names the app reads.
PUBLIC_UPLOAD_MB="${MD_BRIDGE_MAX_UPLOAD_MB:-50}"
PUBLIC_RATE_LIMIT="${MD_BRIDGE_RATE_LIMIT:-60}"
PUBLIC_RATE_WINDOW="${MD_BRIDGE_RATE_WINDOW_SECONDS:-60}"

# These land in a compose file and (the upload cap) in an arithmetic expansion,
# so reject anything but digits first. A value like x[$(cmd)] would otherwise
# execute during $(( )) while this runs as root.
for _var in PUBLIC_UPLOAD_MB PUBLIC_RATE_LIMIT PUBLIC_RATE_WINDOW; do
  case "${!_var}" in
    '' | *[!0-9]*)
      echo "error: $_var must be a non-negative integer, got '${!_var}'" >&2
      exit 1
      ;;
  esac
done
# The app requires a positive upload cap and window (rate limit 0 = disabled),
# so reject 0 here rather than let the API crash on startup. Values are already
# digits-only, so the arithmetic comparison is safe.
if [[ "$PUBLIC_UPLOAD_MB" -lt 1 || "$PUBLIC_RATE_WINDOW" -lt 1 ]]; then
  echo "error: MD_BRIDGE_MAX_UPLOAD_MB and MD_BRIDGE_RATE_WINDOW_SECONDS must be >= 1" >&2
  exit 1
fi

# The token goes into a Compose env_file, where a `$` would be interpolated
# (turning e.g. `$UNSET` into an empty token and silently disabling auth) and
# quotes/backslashes have their own meaning. Restrict it to a charset that is
# literal there. hex/base64/url-safe tokens already fit; reject anything else
# rather than risk a fail-open. Empty (no token) passes and leaves auth off.
case "${MD_BRIDGE_API_TOKEN:-}" in
  *[!A-Za-z0-9._~=+/-]*)
    echo "error: MD_BRIDGE_API_TOKEN may contain only [A-Za-z0-9._~=+/-]" >&2
    echo "       (e.g. openssl rand -hex 24). Regenerate it without other characters." >&2
    exit 1
    ;;
esac

# Caddy rejects an oversized body at the edge before FastAPI spools it. Track
# the app upload cap plus a little multipart overhead. Force base 10 (10#) so a
# value with a leading zero like 050 is not read as octal.
CADDY_MAX_BODY_MB="$((10#$PUBLIC_UPLOAD_MB + 2))"

if [[ -z "$DOMAIN" ]]; then
  echo "error: MD_BRIDGE_DOMAIN is not set" >&2
  echo "usage:  sudo MD_BRIDGE_DOMAIN=example.com $0" >&2
  exit 1
fi

if [[ "$EUID" -ne 0 ]]; then
  echo "error: this script must run as root (use sudo)" >&2
  exit 1
fi

echo "==> Updating apt index"
apt-get update -y >/dev/null

echo "==> Installing prerequisites"
apt-get install -y ca-certificates curl gnupg lsb-release iptables-persistent >/dev/null

echo "==> Adding Docker apt repository"
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update -y >/dev/null

echo "==> Installing Docker Engine + Compose"
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin >/dev/null
systemctl enable --now docker

echo "==> Opening ports 80 and 443"
# OCI Ubuntu images ship with iptables INPUT default DROP; insert allow rules
# before any DROP and persist them across reboots.
for port in 80 443; do
  if ! iptables -C INPUT -p tcp --dport "$port" -j ACCEPT 2>/dev/null; then
    iptables -I INPUT 1 -p tcp --dport "$port" -j ACCEPT
  fi
done
netfilter-persistent save >/dev/null

echo "==> Writing $INSTALL_DIR/compose.yml"
mkdir -p "$INSTALL_DIR"
cat > "$INSTALL_DIR/compose.yml" <<COMPOSE
name: md-bridge

services:
  api:
    image: ghcr.io/vinicq/md-bridge-api:${IMAGE_TAG}
    restart: unless-stopped
    environment:
      PYTHONUNBUFFERED: "1"
      # Public-deploy defenses (see the README "Securing a public deployment").
      # Lower upload cap than the 500 MB local default, and a per-instance
      # request rate limit. The API token lives in api.env (below), not here,
      # so a token with quotes/backslashes needs no YAML escaping.
      MD_BRIDGE_MAX_UPLOAD_MB: "${PUBLIC_UPLOAD_MB}"
      MD_BRIDGE_RATE_LIMIT: "${PUBLIC_RATE_LIMIT}"
      MD_BRIDGE_RATE_WINDOW_SECONDS: "${PUBLIC_RATE_WINDOW}"
    env_file:
      - api.env
    expose:
      - "8000"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/api/health').status==200 else 1)"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s

  web:
    image: ghcr.io/vinicq/md-bridge-web:${IMAGE_TAG}
    restart: unless-stopped
    depends_on:
      api:
        condition: service_healthy
    expose:
      - "80"

  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - api
      - web

volumes:
  caddy_data:
  caddy_config:
COMPOSE

# The API token goes in a root-only env file, referenced by compose env_file.
# Written literally (KEY=VALUE), so a token with quotes or backslashes needs no
# escaping. Create it under umask 077 in a subshell so it is 0600 from the
# moment it exists (no world-readable window before a later chmod). Empty when
# no token was supplied, which leaves auth off.
(umask 077 && printf 'MD_BRIDGE_API_TOKEN=%s\n' "${MD_BRIDGE_API_TOKEN:-}" > "$INSTALL_DIR/api.env")
chmod 600 "$INSTALL_DIR/api.env"

echo "==> Writing $INSTALL_DIR/Caddyfile"
if [[ "$INSECURE" == "1" ]]; then
  cat > "$INSTALL_DIR/Caddyfile" <<CADDY
:80 {
    encode gzip
    # handle, not handle_path: the API serves routes under /api (e.g.
    # /api/health), so the prefix must be preserved. handle_path would strip
    # /api and the upstream would 404.
    handle /api/* {
        # Cap the request body at the edge (matches nginx client_max_body_size
        # and the API 500 MB upload limit) so an oversized upload is rejected
        # before it spools to disk on the VM.
        request_body {
            max_size ${CADDY_MAX_BODY_MB}MiB
        }
        reverse_proxy api:8000
    }
    handle {
        reverse_proxy web:80
    }
}
CADDY
else
  cat > "$INSTALL_DIR/Caddyfile" <<CADDY
$DOMAIN {
    encode gzip
    # handle, not handle_path: the API serves routes under /api (e.g.
    # /api/health), so the prefix must be preserved. handle_path would strip
    # /api and the upstream would 404.
    handle /api/* {
        # Cap the request body at the edge (matches nginx client_max_body_size
        # and the API 500 MB upload limit) so an oversized upload is rejected
        # before it spools to disk on the VM.
        request_body {
            max_size ${CADDY_MAX_BODY_MB}MiB
        }
        reverse_proxy api:8000
    }
    handle {
        reverse_proxy web:80
    }
}
CADDY
fi

echo "==> Starting stack"
cd "$INSTALL_DIR"
docker compose pull
docker compose up -d

echo "==> Writing systemd unit so the stack survives reboots"
cat > /etc/systemd/system/md-bridge.service <<UNIT
[Unit]
Description=md-bridge docker compose stack
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable md-bridge.service

scheme="https"
if [[ "$INSECURE" == "1" ]]; then
  scheme="http"
fi

SMOKE_URL="https://raw.githubusercontent.com/vinicq/md-bridge/${REF}/scripts/smoke.py"

# Post-deploy smoke test.
#
# Insecure mode: the stack answers at http://localhost (Caddy's `:80` block
# serves any Host), so run the smoke now and FAIL the bootstrap if it does
# not pass. Nothing about DNS or TLS can explain a failure in this mode, so
# swallowing it would report a broken deploy as a success.
#
# Secure mode: the domain only answers once DNS points at this VM and Caddy
# has a certificate (step 5 in the README). Aiming the check at $DOMAIN now
# could hit a stale host that still holds the DNS record and print a false
# pass, so do not auto-run; print the command for the operator to run once
# DNS has propagated.
if [[ "$INSECURE" == "1" ]]; then
  echo "==> Running post-deploy smoke test against http://localhost"
  smoke_py="$(mktemp)"
  if ! curl -fsSL "$SMOKE_URL" -o "$smoke_py"; then
    rm -f "$smoke_py"
    echo "error: could not download the smoke test script" >&2
    exit 2
  fi
  if SMOKE_BASE_URL="http://localhost" SMOKE_API_KEY="${MD_BRIDGE_API_TOKEN:-}" \
     python3 "$smoke_py"; then
    echo "==> Smoke test passed"
    rm -f "$smoke_py"
  else
    rm -f "$smoke_py"
    echo "error: smoke test failed against the local stack" >&2
    exit 2
  fi
fi

echo
echo "==================================================================="
echo "md-bridge is up at $scheme://$DOMAIN"
echo "Caddy will fetch a Let's Encrypt cert on the first browser visit."
if [[ "$INSECURE" != "1" ]]; then
  echo
  echo "Once DNS points $DOMAIN at this VM, verify the deploy end to end:"
  echo "  curl -fsSL $SMOKE_URL -o smoke.py"
  if [[ -n "${MD_BRIDGE_API_TOKEN:-}" ]]; then
    echo "  SMOKE_BASE_URL=https://$DOMAIN SMOKE_API_KEY=<your-token> python3 smoke.py"
  else
    echo "  SMOKE_BASE_URL=https://$DOMAIN python3 smoke.py"
  fi
fi
echo "==================================================================="
