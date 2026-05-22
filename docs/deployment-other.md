# Deployment recipes

md-bridge ships a Docker Compose stack that runs anywhere Docker
runs. This page collects walkthroughs for the three platform-as-a-service
hosts contributors ask about most often: Render, Fly.io, and
Railway. Each has its own sweet spot.

| Host | Sweet spot | Trade-off |
|---|---|---|
| **Render** | Cheapest path from zero to a live URL; free tier accepts Docker Compose verbatim | Services sleep after 15 min idle, 30-second cold start, 750 free hours/month |
| **Fly.io** | Global edge presence, fly.toml is the manifest | No free tier today; pay-as-you-go from the first machine-hour |
| **Railway** | Fastest "click and deploy" once you have the GitHub repo connected | $5/month minimum after 30-day trial |

All three use the public images on GHCR
(`ghcr.io/vinicq/md-bridge-api:latest` and
`ghcr.io/vinicq/md-bridge-web:latest`), so you do not have to build
or push your own. The images are multi-arch (linux/amd64 and
linux/arm64) and self-contained: no external runtime dependencies,
no telemetry, no outbound network calls after start.

## Render

Render reads `render.yaml` from the repo root. The free plan accepts
two services per blueprint, which matches md-bridge's `api + web`
split.

### Steps

1. **Fork or clone the repo** to your own GitHub account.
2. **Create a Render account** at <https://render.com> and connect
   the GitHub account holding your fork.
3. **New Blueprint** from the dashboard. Pick the fork; Render
   detects `render.yaml` if present (see "Blueprint" section below
   for the file to commit). If you do not want to fork, you can
   define two services manually:
   - Service 1: `api` — Docker image
     `ghcr.io/vinicq/md-bridge-api:latest`, port `8000`,
     health check path `/api/health`.
   - Service 2: `web` — Docker image
     `ghcr.io/vinicq/md-bridge-web:latest`, port `80`, health
     check path `/`.
4. **Set the env var** on the `web` service:
   `VITE_API_URL=https://<your-api-service>.onrender.com`. The
   frontend reads this at build time, so the value has to be
   present before the first deploy.
5. **Deploy**. The first deploy takes 5-10 minutes per service
   because Render pulls the multi-arch image cold.
6. **Verify** with `curl https://<your-api-service>.onrender.com/api/health`.
   Expect `{"status":"ok"}` after the cold start finishes.

### Blueprint (`render.yaml` at repo root)

```yaml
services:
  - type: web
    name: md-bridge-api
    runtime: image
    image:
      url: ghcr.io/vinicq/md-bridge-api:latest
    healthCheckPath: /api/health
    plan: free
    envVars:
      - key: PORT
        value: "8000"

  - type: web
    name: md-bridge-web
    runtime: image
    image:
      url: ghcr.io/vinicq/md-bridge-web:latest
    healthCheckPath: /
    plan: free
    envVars:
      - key: VITE_API_URL
        sync: false  # set in the dashboard to the api service URL
```

### Free-tier caveats to write down up front

- Services sleep after **15 minutes idle**. The next request takes
  about 30 seconds to wake the container.
- The free quota is **750 service-hours/month**, shared across all
  free services on your account. Two services running 24/7
  consume the full quota by day 16. Sleep counts in your favor.
- Render does not honor `Content-Length` requests larger than 100
  MB on the free plan by default. Large PDF uploads need a paid
  plan or a chunked-upload workaround.

### Reversibility

Delete the services from the Render dashboard. The GHCR images
remain untouched. Your data is gone because md-bridge stores
nothing (see the [FAQ](faq.md) on persistence).

## Fly.io

Fly reads `fly.toml` and `Dockerfile`. md-bridge's existing
`apps/api/Dockerfile` is the right starting point; the web service
gets its own `apps/web/Dockerfile`.

### Steps

1. **Install the CLI**:

   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Sign in**:

   ```bash
   fly auth signup    # or `fly auth login`
   ```

3. **Launch the API**:

   ```bash
   cd apps/api
   fly launch --image ghcr.io/vinicq/md-bridge-api:latest --no-deploy
   ```

   The launcher walks you through name, region, and `fly.toml`
   creation. Pick the region nearest your users; Fly defaults to
   the region you ran the CLI from.

4. **Edit `fly.toml`** to set the internal port and the health
   check:

   ```toml
   app = "md-bridge-api-<yourname>"
   primary_region = "gru"  # São Paulo, change to suit

   [build]
     image = "ghcr.io/vinicq/md-bridge-api:latest"

   [http_service]
     internal_port = 8000
     force_https = true
     auto_stop_machines = "stop"
     auto_start_machines = true
     min_machines_running = 0

   [[http_service.checks]]
     interval = "30s"
     timeout = "5s"
     method = "GET"
     path = "/api/health"
   ```

5. **Deploy**:

   ```bash
   fly deploy
   ```

6. **Launch the web app** the same way from `apps/web/`, with
   `internal_port = 80` and the env var
   `VITE_API_URL=https://md-bridge-api-<yourname>.fly.dev`. The
   env var is set during build, so use
   `fly deploy --build-arg VITE_API_URL=...` or bake it into the
   image you push.

7. **Verify**:

   ```bash
   curl https://md-bridge-api-<yourname>.fly.dev/api/health
   ```

### Why `auto_stop_machines = "stop"`

This is the Fly equivalent of Render's idle sleep. The machine
shuts down after a few minutes of no traffic and wakes on the
next request. Cost stays near zero for projects with bursty
traffic. Cold-start latency on Fly is faster than Render (under
5 seconds), but still visible if your audience expects instant.

### Reversibility

```bash
fly apps destroy md-bridge-api-<yourname>
fly apps destroy md-bridge-web-<yourname>
```

Both commands are idempotent and immediate.

## Railway

Railway is the most opinionated of the three. The CLI is optional;
the dashboard does everything.

### Steps

1. **Sign up** at <https://railway.app> with the GitHub account
   holding your fork (or with email and connect later).
2. **New Project → Empty Project**.
3. **Add Service → From Docker Image**:
   - Image: `ghcr.io/vinicq/md-bridge-api:latest`
   - Internal port: `8000`
   - Service name: `api`
4. **Add Service → From Docker Image** again, for the web:
   - Image: `ghcr.io/vinicq/md-bridge-web:latest`
   - Internal port: `80`
   - Service name: `web`
   - Environment variable: `VITE_API_URL` pointing to the public
     URL of the `api` service (Railway generates the URL when you
     enable "Public Networking" on the api service).
5. **Settings → Networking → Generate Domain** on both services.
6. **Verify** with `curl https://<api-domain>/api/health`.

### Costs

Railway has no permanent free tier. The $5/month "Hobby" plan
gives 500 execution hours and 100 GB of bandwidth. Two services
with auto-sleep stay well under the cap; two services running
24/7 with traffic will go over.

### Reversibility

In the project dashboard, **Settings → Delete Project**. Two
clicks, no charge if you delete before the next billing cycle.

## Common gotchas across all three

These bite the same way on Render, Fly.io, and Railway, so worth
calling out once.

### 1. `VITE_API_URL` is a build-time variable

The frontend embeds the API URL in the bundle during `vite build`.
If you change the API host later, you have to rebuild and redeploy
the web service. Setting `VITE_API_URL` after the fact in the
runtime environment does nothing because the bundle is already
built.

### 2. The web service has no API itself

The web container only serves static files plus a tiny nginx
config. It does not proxy to the API. If you want to hide the API
behind the web domain (single-origin, no CORS), put a reverse
proxy in front (Render's "rewrites" feature, Fly's
`http_options.response.headers`, Railway's "Custom Domain" with a
path rewrite), or bake the proxy into your own derivative image.

### 3. CORS

When the web and api services live on different hostnames, the
browser blocks API calls unless the API allows the web origin.
Set `MD_BRIDGE_CORS_ORIGINS` on the api service:

```bash
MD_BRIDGE_CORS_ORIGINS="https://md-bridge-web.example.com"
```

On Render, set this in the Dashboard → Environment for the api
service. On Fly, add it to the `[env]` block in `fly.toml`. On
Railway, Variables tab on the api service.

### 4. Cold starts hide test failures

The first request after a sleep cycle warms the container. If you
hit `/api/pdf-to-md` cold with a 50 MB PDF, the request can time
out at the platform's edge (Render's 100s timeout, Railway's
default 30s) even though the conversion succeeds eventually. Warm
the service with a `GET /api/health` request first, especially
for any CI smoke test that hits the live deploy.

### 5. The 500 MB upload cap is on the API, not the platform

md-bridge caps every upload at 500 MB
(`apps/api/app/config.py:MAX_UPLOAD_BYTES`). Render, Fly, and
Railway all have their own caps that are typically smaller (100
MB on most free plans). Whichever is tighter wins; if you need
the full 500 MB, check the platform's body-size policy first.

## When none of the three fit

The Docker Compose stack also runs on:

- **Self-hosted VPS** (Hetzner, DigitalOcean, Linode, Vultr). The
  recipe is "ssh in, install Docker, `docker compose up -d`".
- **AWS / GCP / Azure** via their managed container services
  (App Runner, Cloud Run, Container Apps). The images go on GHCR
  or you mirror them to the cloud-native registry; the rest is
  vendor-specific clickops.
- **Kubernetes** for teams that already have a cluster. The
  Helm chart is a backlog item; for now the pattern is
  "Deployment + Service for `api`, Deployment + Service +
  Ingress for `web`, env var for `VITE_API_URL`".

If you have a deployment recipe for a host that is not covered
here, the contributing guide covers how to land it as a doc PR.
The shape used here (steps, blueprint or manifest, free-tier
caveats up front, reversibility) is the template to match.
