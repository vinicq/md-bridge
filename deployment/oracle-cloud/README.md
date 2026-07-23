# Deploy md-bridge on Oracle Cloud Always Free

This recipe brings md-bridge up on a **free-forever** Oracle Cloud
Infrastructure (OCI) ARM Ampere A1 VM and serves it over HTTPS at a
domain of your choice. Total cost: **US$0**. Total time: **30-45
minutes** including the OCI signup.

The flow is split in five steps. Each step says what you do in the
browser and what runs on the VM.

- [What you get](#what-you-get)
- [What you need](#what-you-need)
- [1. Create the OCI Always Free account](#1-create-the-oci-always-free-account)
- [2. Provision the VM](#2-provision-the-vm)
- [3. Open ports 80 and 443](#3-open-ports-80-and-443)
- [4. Bootstrap the VM](#4-bootstrap-the-vm)
- [5. Point your domain at the VM](#5-point-your-domain-at-the-vm)
- [Updating to a newer release](#updating-to-a-newer-release)
- [Tearing it down](#tearing-it-down)

## What you get

- One ARM Ampere A1 VM with **4 OCPU + 24 GB RAM** (always free).
- Ubuntu 22.04 LTS.
- Docker Engine + Docker Compose pulling pre-built images from GHCR
  (`ghcr.io/vinicq/md-bridge-api` and `-web`).
- [Caddy](https://caddyserver.com/) as a reverse proxy in front of the
  stack. Caddy automates Let's Encrypt certificates and renewals.
- HTTPS on your domain.

## What you need

- An e-mail address and a credit card. Oracle uses the card to verify
  you are a human; it will **not** be charged for Always Free
  resources.
- A domain you control (optional but recommended). Free options:
  [DuckDNS](https://www.duckdns.org/) (subdomain like
  `mdbridge.duckdns.org`), [No-IP](https://www.noip.io/),
  [Cloudflare-registered domain](https://www.cloudflare.com/products/registrar/).
  Skip this step and serve over the public IP if you only want a
  proof-of-life demo.
- A way to SSH (OpenSSH on macOS / Linux, or
  `ssh.exe` on Windows 10/11).

## 1. Create the OCI Always Free account

1. Open <https://signup.cloud.oracle.com/>.
2. Pick the **home region nearest to you** (you cannot change this
   later, and ARM Ampere A1 capacity varies by region; São Paulo, US
   East Ashburn, and Frankfurt usually have stock).
3. Complete the signup. Verify your e-mail, enter the credit card,
   wait for the "Your account is ready" e-mail.
4. Sign in to <https://cloud.oracle.com>.

## 2. Provision the VM

In the OCI console:

1. Top-left hamburger → **Compute → Instances → Create instance**.
2. Name: `md-bridge`.
3. **Image and shape**:
   - Image: `Canonical Ubuntu 22.04`.
   - Shape: click **Change shape** → **Ampere** → `VM.Standard.A1.Flex`
     → set **4 OCPU** and **24 GB memory**.
4. **Networking**: accept the auto-created VCN and subnet.
   Tick **"Assign a public IPv4 address"**.
5. **SSH key**:
   - On your laptop, create one if you have not already:
     ```bash
     ssh-keygen -t ed25519 -C "md-bridge"
     # default location is fine: ~/.ssh/id_ed25519
     ```
   - In the console, choose **Paste public keys** and paste the
     contents of `~/.ssh/id_ed25519.pub`.
6. **Boot volume**: default (50 GB is enough).
7. Click **Create**. Wait ~60 seconds.
8. When status is **Running**, copy the **Public IP address** shown in
   the instance details. You will use it for SSH and DNS.

## 3. Open ports 80 and 443

Out of the box, the VCN's default Security List only permits SSH
(port 22). Caddy needs 80 and 443.

1. From the instance page, click the **Virtual cloud network** link.
2. In the VCN page, click **Security Lists** → **Default Security List
   for &lt;your-vcn-name&gt;**.
3. **Add Ingress Rules**:
   - Source: `0.0.0.0/0`. Destination Port Range: `80`. Description:
     `HTTP for Caddy challenge + redirect`.
   - Source: `0.0.0.0/0`. Destination Port Range: `443`. Description:
     `HTTPS`.
4. Click **Add Ingress Rules** to save both.

You also need to open the same ports on the OS-level firewall (Ubuntu
runs iptables by default on OCI Ubuntu images). The bootstrap script
in the next step does that for you.

## 4. Bootstrap the VM

SSH in:

```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@<PUBLIC_IP>
```

Download and run the bootstrap script:

```bash
curl -fsSL https://raw.githubusercontent.com/vinicq/md-bridge/main/deployment/oracle-cloud/bootstrap.sh -o bootstrap.sh
chmod +x bootstrap.sh
sudo MD_BRIDGE_DOMAIN="<your.domain.com>" ./bootstrap.sh
```

If you don't have a domain yet, pass the public IP instead and Caddy
will run on HTTP only:

```bash
sudo MD_BRIDGE_DOMAIN="<PUBLIC_IP>" MD_BRIDGE_INSECURE=1 ./bootstrap.sh
```

The script:

- Installs Docker Engine and the compose plugin from the official
  Docker apt repository.
- Opens ports 80 and 443 in `iptables` and persists the rules with
  `iptables-persistent`.
- Pulls the latest md-bridge API and Web images from GHCR.
- Writes a `compose.yml` and a `Caddyfile` under `/opt/md-bridge/`.
- Starts the stack with `systemd` so it survives reboots.

Wait for the script to print **"md-bridge is up at https://&lt;domain&gt;"**.

## 5. Point your domain at the VM

If you used a real domain, create an **A record** that maps it to the
VM's public IP:

- Cloudflare or any DNS provider: add an A record
  `mdbridge.example.com -> <PUBLIC_IP>`, TTL 60 seconds.
- DuckDNS: log in, paste the IP in the **current ip** box.

Wait one or two minutes for propagation, then open
`https://mdbridge.example.com` in a browser. Caddy will fetch a
Let's Encrypt certificate on the first request (15-30 seconds).

## Updating to a newer release

SSH in and pull the new images:

```bash
cd /opt/md-bridge
sudo docker compose pull
sudo docker compose up -d
```

The compose file pins `:latest`, so any release published by the
`docker-publish.yml` workflow on GitHub becomes available within
minutes.

After updating, re-run the smoke test to confirm the new images serve:

```bash
curl -fsSL https://raw.githubusercontent.com/vinicq/md-bridge/main/scripts/smoke.py -o smoke.py
SMOKE_BASE_URL="https://<your.domain>" python3 smoke.py
# If you set MD_BRIDGE_API_TOKEN, also export SMOKE_API_KEY=<token> so the
# guarded md-to-pdf check is authorized (otherwise it returns 401).
```

## Rolling back

`:latest` always pulls the newest image, so to pin a known-good version (or
undo a bad update) set an explicit tag and bring the stack up on it. Every
release is tagged by semver and by commit SHA
(`ghcr.io/vinicq/md-bridge-api:0.11.0`, `...:sha-<7hex>`).

Edit `/opt/md-bridge/compose.yml`, replace the two `:latest` image tags with
the version you want, then:

```bash
cd /opt/md-bridge
sudo docker compose pull && sudo docker compose up -d
```

Or re-run the bootstrap with the tag pinned. It is not left on the box, so
download it again, and it needs your domain:

```bash
curl -fsSL https://raw.githubusercontent.com/vinicq/md-bridge/main/deployment/oracle-cloud/bootstrap.sh -o bootstrap.sh
sudo MD_BRIDGE_DOMAIN="<your.domain>" MD_BRIDGE_IMAGE_TAG=0.11.0 ./bootstrap.sh
```

GHCR tags are mutable: a workflow rerun can move a tag to a new digest. The
`sha-<commit>` tag is the most stable handle; for a guaranteed-identical
rollback, pin by digest instead:

```bash
docker buildx imagetools inspect ghcr.io/vinicq/md-bridge-api:0.11.0   # find the sha256
# then use ghcr.io/vinicq/md-bridge-api@sha256:... in compose.yml
```

## Diagnosing a problem

Everything an operator needs is on the box, no external service:

```bash
cd /opt/md-bridge
sudo docker compose ps                     # up / restarting / unhealthy
sudo docker compose logs --tail=200 api    # api access log: method, path, status, duration
sudo docker compose logs --tail=200 caddy web
# Liveness. Use the public URL (Caddy routes by domain, so http://localhost
# does not match the site), or hit the api container directly, which needs
# neither Caddy nor DNS:
curl -fsS https://<your.domain>/api/health
sudo docker compose exec api \
  python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/api/health').read())"
```

The API logs one line per `/api` request (method, path, status, duration),
including failures and timeouts, and never the document content. Status codes
worth knowing: `422 too_many_pages` (PDF over `MD_BRIDGE_MAX_PDF_PAGES`),
`503 service_busy` (at capacity or the wait queue is full), and
`504 conversion_timeout` (hit `MD_BRIDGE_CONVERT_TIMEOUT_SECONDS`).

## Backing up the configuration

The only per-host state lives under `/opt/md-bridge` (there is no database
and no stored documents). Back up:

- `compose.yml` (the stack definition and env values)
- `Caddyfile` (the proxy config and domain)
- `api.env` (the API token, mode 0600)

The archive contains the token, so lock it down to root-only:

```bash
sudo tar czf md-bridge-config.tgz -C /opt md-bridge/compose.yml md-bridge/Caddyfile md-bridge/api.env
sudo chmod 600 md-bridge-config.tgz
```

Caddy's `caddy_data` volume holds the Let's Encrypt certificates; it is
re-fetched automatically on a fresh host, so it is optional to back up.

## Securing a public deployment

A public instance accepts uploads and drives Chromium and PyMuPDF, so it
spends CPU and disk on behalf of anyone who can reach it. The bootstrap
compose already ships three defenses, all env-driven, all off in a bare
local run:

| Env var | Bootstrap default | Effect |
|---|---|---|
| `MD_BRIDGE_MAX_UPLOAD_MB` | `50` | Public upload cap, below the 500 MB code default. Caddy rejects bodies over this plus ~2 MiB (52 MiB at the default) at the edge before they spool. |
| `MD_BRIDGE_RATE_LIMIT` | `60` | Requests per window before the conversion routes answer `429`. `0` disables it. |
| `MD_BRIDGE_RATE_WINDOW_SECONDS` | `60` | Length of that window. |
| `MD_BRIDGE_API_TOKEN` | unset | If set, the conversion routes require a matching `X-API-Key` header. |

Set a token before bootstrapping to require a key on every conversion:

```bash
sudo MD_BRIDGE_DOMAIN="mdbridge.example.com" \
     MD_BRIDGE_API_TOKEN="$(openssl rand -hex 24)" ./bootstrap.sh
```

Two limits worth knowing:

- **Setting a token disables the bundled UI, on purpose.** The web UI sends
  its conversion requests without an `X-API-Key` (an anonymous browser has no
  key), so once `MD_BRIDGE_API_TOKEN` is set, every conversion from the
  bundled pages returns 401. The token is for an **API-only** deployment
  (curl, scripts, CI). Choose one of two modes:
    - **Public UI + abuse protection**: leave `MD_BRIDGE_API_TOKEN` unset and
      rely on the rate limit and upload cap. The pages work for anyone; the
      limits keep the box safe.
    - **Locked surface (UI included)**: leave the app token unset and put
      basic-auth or SSO at Caddy (`basic_auth` in the Caddyfile, or an
      `oauth2-proxy` container in front). That gates the HTML and the API with
      one credential the browser actually sends. Set the app token too only if
      you also want a separate key for programmatic clients.
- **The rate limit is per instance by default.** Counters live in the API
  process, and behind Caddy every request arrives from Caddy's address, so
  the limit throttles total load on the box rather than per client IP. That
  protects the instance, which is the goal. For true per-IP limiting, run
  uvicorn with `--forwarded-allow-ips` and have Caddy set `X-Forwarded-For`
  to the real client; a shared store for multi-instance counters is out of
  scope (self-hosted, no external state).

### Manual test (denied access and rate-limit exceeded)

With a token set and `MD_BRIDGE_RATE_LIMIT=60`:

```bash
# Denied: no key -> 401
curl -s -o /dev/null -w "%{http_code}\n" \
  -F "file=@notes.md" https://mdbridge.example.com/api/md-to-pdf   # 401

# Allowed: correct key -> 200
curl -s -o /dev/null -w "%{http_code}\n" -H "X-API-Key: <token>" \
  -F "file=@notes.md" https://mdbridge.example.com/api/md-to-pdf   # 200

# Rate limit: hammer past the window cap -> a 429 appears
for i in $(seq 1 70); do
  curl -s -o /dev/null -w "%{http_code} " -H "X-API-Key: <token>" \
    -F "file=@notes.md" https://mdbridge.example.com/api/md-to-pdf
done; echo   # trailing codes turn to 429
```

## Tearing it down

- Console → Compute → Instances → click `md-bridge` → **More
  actions** → **Terminate**. Confirm.
- Optional: delete the VCN from **Networking → Virtual cloud
  networks**.
- Optional: revoke the SSH key from your local `~/.ssh/known_hosts`.

The Always Free tier covers up to **2 ARM Ampere A1 VMs per tenancy**
with 4 OCPU / 24 GB shared between them. You can spin up another one
the same way at any time.
