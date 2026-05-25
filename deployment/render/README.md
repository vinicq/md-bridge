# Deploy to Render (free tier)

Render is the cheapest path from zero to a live md-bridge URL. The free
plan accepts the existing `render.yaml` blueprint verbatim, and the two
services (`api` + `web`) fit inside the free-plan allowance.

Read this whole page before you click "New Blueprint", especially the
[free-tier caveats](#free-tier-caveats) section. Two of those caveats
will surprise you the first time you hit them.

## What you need

- A GitHub account
- A Render account at <https://render.com>
- Your own fork (or clone) of `vinicq/md-bridge`. Render reads
  `render.yaml` from the repo root, so the fork has to include it; the
  upstream repo already does

You do not need to build or push container images. The blueprint pulls
the public GHCR images at `ghcr.io/vinicq/md-bridge-api:latest` and
`ghcr.io/vinicq/md-bridge-web:latest`. Both are multi-arch
(`linux/amd64` and `linux/arm64`).

## Steps

1. **Fork the repo** to your own GitHub account if you haven't already.
2. **Create a Render account** and connect the GitHub account holding
   your fork.
3. **New Blueprint** from the dashboard. Pick the fork. Render auto-
   detects `render.yaml` at the repo root and proposes both services.
4. **Set `VITE_API_URL` on the `md-bridge-web` service** to
   `https://<your-api-service>.onrender.com`. The frontend reads this
   at build time, so it has to be set before the first deploy or the
   web service ships pointing at the wrong URL.
5. **Deploy**. The first deploy takes 5 to 10 minutes per service
   because Render pulls the multi-arch image cold.
6. **Verify** with `curl https://<your-api-service>.onrender.com/api/health`.
   Expect `{"status":"ok"}` after the cold start finishes.

If you'd rather skip the fork, you can also define the two services
manually in the Render dashboard:

- **api**: Docker image `ghcr.io/vinicq/md-bridge-api:latest`, port
  `8000`, health check path `/api/health`
- **web**: Docker image `ghcr.io/vinicq/md-bridge-web:latest`, port
  `80`, health check path `/`

## The blueprint

`render.yaml` lives at the repo root and looks like this:

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

The `sync: false` on `VITE_API_URL` is intentional. Render does not
rebuild blueprint env vars across deploys, so the value has to live in
the dashboard.

## Free-tier caveats

These are not "gotchas to discover the hard way", they are written into
Render's free plan.

- **Services sleep after 15 minutes idle.** The next request after
  sleep takes about 30 seconds to wake the container. A user opening
  the site for the first time after lunch is going to wait 30 seconds.
- **750 service-hours per month** shared across all free services on
  your account. Two services running 24/7 consume the quota by day 16.
  The sleep behavior above works in your favor here.
- **No `Content-Length` above 100 MB** on the free plan. Large PDF
  uploads either need a paid plan or a chunked-upload workaround on the
  client.

## Tearing it down

Delete both services from the Render dashboard. The public GHCR images
stay untouched. md-bridge stores nothing server-side (see the
[FAQ](https://vinicq.github.io/md-bridge/faq/) on persistence), so there
is no data to clean up.

## Other hosts

If Render's free-tier limits do not fit your use case, the
[other deployment recipes](https://vinicq.github.io/md-bridge/deployment-other/)
cover Fly.io and Railway. The Oracle Cloud Always Free walkthrough at
[`deployment/oracle-cloud/`](https://github.com/vinicq/md-bridge/tree/main/deployment/oracle-cloud)
is the reference pattern for self-managed VMs.
