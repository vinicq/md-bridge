# syntax=docker/dockerfile:1.7

# ---- Stage 1: install dependencies ----------------------------------------
# Pinned to node 24 (the major CI and local dev use). Do NOT bump to node 26:
# vitest's jsdom env leaves window.localStorage undefined there, failing every
# DOM test. CI runs vitest directly (not this image), so that regression would
# only surface when someone builds the `--profile test` runner by hand.
FROM node:26-alpine@sha256:e88a35be04478413b7c71c455cd9865de9b9360e1f43456be5951032d7ac1a66 AS deps
WORKDIR /web

# Cache npm deps separately from source changes. Use `npm ci` so the image
# resolves the exact lockfile versions (reproducible, matches CI and local),
# rather than letting `npm install` drift to newer ranges inside the container.
COPY apps/web/package.json apps/web/package-lock.json /web/
RUN npm ci --no-audit --no-fund --no-progress

# ---- Stage 2: source -------------------------------------------------------
# Shared by build and test so the source layer is materialized once.
FROM deps AS source
COPY apps/web/ /web/

# ---- Stage 3: build the React app -----------------------------------------
FROM source AS build
RUN npm run build

# ---- Stage 4: test ---------------------------------------------------------
# Runs vitest (unit + integration) inside Docker via the compose `test`
# profile. Playwright end-to-end tests are not part of this stage; they need
# a running backend and a real browser session, so they live in CI and in
# `npm run test:e2e` locally.
FROM source AS test
CMD ["npm", "run", "test"]

# ---- Stage 5: serve the static bundle via nginx (default runtime) ---------
FROM nginx:1.31-alpine@sha256:54f2a904c251d5a34adf545a72d32515a15e08418dae0266e23be2e18c66fefa AS runtime
COPY --from=build /web/dist /usr/share/nginx/html
COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://localhost/ || exit 1
