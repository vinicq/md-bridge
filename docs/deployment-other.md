# Deploying to other hosts

The [recommended setup](deployment/oracle-cloud.md) runs the Docker
Compose stack behind Caddy on a single host: web and API share one
origin, Caddy proxies `/api/*` to the API container, and there is no CORS
to configure. That pattern is the whole deployment story. This page covers
running it on hosts other than Oracle Cloud.

## The one rule: keep web and API same-origin

md-bridge's frontend calls the API at relative paths (`/api/...`). There
is no build-time API URL to set. Whatever host you pick, put a reverse
proxy in front so a single hostname serves the UI and forwards `/api/*` to
the API container. The shipped `web` image already does this: its nginx
proxies `/api/` to the `api` service, the same job Caddy does in the
recommended recipe.

Split the two services onto separate hostnames and you inherit two
problems the same-origin setup does not have: an API URL baked into the
frontend bundle at build time, and CORS. Keep one origin and neither
exists.

The proxy must forward the full path. The API serves every route under
`/api` (`/api/health`, `/api/md-to-pdf`, and so on), so a proxy that
strips the `/api` prefix before forwarding returns 404 for every call.
Caddy's `handle /api/*` and nginx's `location /api/` both preserve the
prefix; Caddy's `handle_path` strips it, so do not use it here.

## Self-managed VPS (Hetzner, DigitalOcean, Linode, Vultr)

Same recipe as the Oracle Cloud one, minus the OCI account and firewall
steps:

1. Create a small VM with a public IP and open ports 80 and 443.
2. Install Docker and the compose plugin.
3. Copy `deployment/oracle-cloud/bootstrap.sh` to the box and run it, or
   run the commands it contains by hand.
4. Point a domain at the VM and let Caddy fetch a certificate.

`bootstrap.sh` targets Ubuntu: it uses `apt-get`, Docker's Ubuntu package
repository, `iptables-persistent`, and systemd. On another Ubuntu (or
Debian-family) VM it runs as-is; on a provider whose firewall lives in a
cloud console, open 80/443 there and drop the iptables lines. On a
non-Debian distro, install Docker yourself and run the compose stack behind
Caddy by hand, following the same same-origin pattern the script sets up.

## Managed container platforms (Cloud Run, App Runner, Container Apps)

They run the same GHCR images (`ghcr.io/vinicq/md-bridge-api` and `-web`),
so the image is never the problem. The catch is the same-origin rule:
most managed platforms give each container its own hostname. To keep one
origin you have two options.

- Deploy both images but expose only the `web` service publicly, and let
  its nginx reach the API over the platform's internal network. The shipped
  `apps/web/nginx.conf` hardcodes `proxy_pass http://api:8000`, so the API
  service must be reachable at the hostname `api` on port 8000. Give the API
  service that name (or a network alias) on the platform, or rebuild the web
  image with your API's address baked into `nginx.conf`. Platforms that
  assign a fixed generated hostname you cannot alias will hit an nginx
  resolution error.
- Put the platform's own path router in front, mapping `/api/*` to the API
  service and everything else to the web service, preserving the `/api`
  prefix.

If the platform can express neither, you are back to the two-origin
problems above. Pick one that can, or use a VM.

## Kubernetes

For teams that already run a cluster: a Deployment plus Service for `api`,
a Deployment plus Service for `web`, and an Ingress that routes `/api/*`
to the api Service (prefix preserved) and `/` to the web Service.
Same-origin holds as long as both sit behind one Ingress host. A Helm
chart is on the backlog.

## Verifying any deploy

Every recipe ends the same way: run the smoke test against the live URL.
It checks `GET /api/health` and a small `POST /api/md-to-pdf` over real
HTTP. Exit 0 means the deploy serves the app; exit 1 means something in
the chain (proxy, API, or renderer) is broken.

From a repository checkout:

```bash
SMOKE_BASE_URL="https://your.domain" python3 scripts/smoke.py
```

On a host that only has the images (no checkout), download the script
first:

```bash
curl -fsSL https://raw.githubusercontent.com/vinicq/md-bridge/main/scripts/smoke.py -o smoke.py
SMOKE_BASE_URL="https://your.domain" python3 smoke.py
```

The Oracle Cloud `bootstrap.sh` downloads and runs it for you in insecure
mode; in secure mode it prints the command to run once DNS points at the
new host.
