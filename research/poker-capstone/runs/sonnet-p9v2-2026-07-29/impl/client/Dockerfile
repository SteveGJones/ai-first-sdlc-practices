# Poker Capstone — client
#
# Static React/TypeScript build served by nginx on container port 80, per
# docs/HARNESS-CONTRACT.md's packaging note ("If a client is submitted, its
# service must be named `client`... container port [80]"). This Dockerfile
# does not define a docker-compose.yml — the server this client talks to is
# chosen/composed separately.

# ---- build stage -----------------------------------------------------
FROM node:20-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY tsconfig.json vite.config.ts index.html ./
COPY public ./public
COPY src ./src
RUN npm run build

# ---- serve stage ------------------------------------------------------
FROM nginx:1.27-alpine AS serve

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80

# Optional: point the browser at a server published on a different
# host:port than the same-origin default (see src/api.ts getApiBase()).
ENV API_BASE=""

ENTRYPOINT ["/docker-entrypoint.sh"]
