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

echo "==> Writing $INSTALL_DIR/Caddyfile"
if [[ "$INSECURE" == "1" ]]; then
  cat > "$INSTALL_DIR/Caddyfile" <<CADDY
:80 {
    encode gzip
    handle_path /api/* {
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
    handle_path /api/* {
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

# Smoke test: wait up to 60 s for the API to answer.
echo "==> Waiting for the stack to come up"
for i in $(seq 1 30); do
  if curl -fsS "http://localhost:80/api/health" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

scheme="https"
if [[ "$INSECURE" == "1" ]]; then
  scheme="http"
fi

echo
echo "==================================================================="
echo "md-bridge is up at $scheme://$DOMAIN"
echo "Caddy will fetch a Let's Encrypt cert on the first browser visit."
echo "==================================================================="
