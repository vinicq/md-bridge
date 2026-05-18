# syntax=docker/dockerfile:1.7

# ---- Stage 1: build the React app ----
FROM node:22-alpine AS build
WORKDIR /web

# Cache npm deps separately from source changes.
COPY apps/web/package.json apps/web/package-lock.json /web/
RUN npm install --no-audit --no-fund --no-progress

COPY apps/web/ /web/
RUN npm run build

# ---- Stage 2: serve the static bundle via nginx ----
FROM nginx:1.27-alpine
COPY --from=build /web/dist /usr/share/nginx/html
COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://localhost/ || exit 1
