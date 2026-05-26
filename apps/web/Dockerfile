# syntax=docker/dockerfile:1.7

# ---- Stage 1: install dependencies ----------------------------------------
FROM node:26-alpine@sha256:e71ac5e964b9201072425d59d2e876359efa25dc96bb1768cb73295728d6e4ea AS deps
WORKDIR /web

# Cache npm deps separately from source changes.
COPY apps/web/package.json apps/web/package-lock.json /web/
RUN npm install --no-audit --no-fund --no-progress

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
FROM nginx:1.31-alpine@sha256:8b1e78743a03dbb2c95171cc58639fef29abc8816598e27fb910ed2e621e589a AS runtime
COPY --from=build /web/dist /usr/share/nginx/html
COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://localhost/ || exit 1
