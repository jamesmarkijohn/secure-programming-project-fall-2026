# Built from the repo root (see docker-compose.yml).

FROM node:24-alpine AS build
WORKDIR /app
COPY src/frontend/package.json src/frontend/package-lock.json ./
RUN npm ci
COPY src/frontend/ .
RUN npm run build

FROM caddy:2-alpine
COPY src/frontend/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/dist /srv
