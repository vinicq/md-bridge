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

## Self-managed VPS (Hetzner, DigitalOcean, Linode, Vultr)

Same recipe as the Oracle Cloud one, minus the OCI account and firewall
steps:

1. Create a small VM with a public IP and open ports 80 and 443.
2. Install Docker and the compose plugin.
3. Copy `deployment/oracle-cloud/bootstrap.sh` to the box and run it, or
   run the commands it contains by hand.
4. Point a domain at the VM and let Caddy fetch a certificate.

`bootstrap.sh` is host-agnostic apart from the iptables step. On a
provider whose firewall lives in a cloud console, open 80/443 there and
skip the local iptables lines.

## Managed container platforms (Cloud Run, App Runner, Container Apps)

They run the same GHCR images (`ghcr.io/vinicq/md-bridge-api` and `-web`),
so the image is never the problem. The catch is the same-origin rule:
most managed platforms give each container its own hostname. To keep one
origin, either

- deploy only the `web` image and let its built-in nginx proxy reach the
  API over the platform's internal networking, or
- put the platform's own path router in front, mapping `/api/*` to the API
  service and everything else to the web service.

If the platform cannot express a path rewrite, you are back to the
two-origin problems above. Pick one that can, or use a VM.

## Kubernetes

For teams that already run a cluster: a Deployment plus Service for `api`,
a Deployment plus Service for `web`, and an Ingress that routes `/api/*`
to the api Service and `/` to the web Service. Same-origin holds as long
as both sit behind one Ingress host. A Helm chart is on the backlog.

## Verifying any deploy

Every recipe ends the same way: run the smoke test against the live URL.

```bash
SMOKE_BASE_URL="https://your.domain" python3 scripts/smoke.py
```

It checks `GET /api/health` and a small `POST /api/md-to-pdf` over real
HTTP. Exit 0 means the deploy serves the app; exit 1 means something in
the chain (proxy, API, or renderer) is broken.
</content>
</invoke>
