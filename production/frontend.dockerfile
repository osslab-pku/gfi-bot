FROM node:16 AS builder

COPY ./ /gfi-bot
WORKDIR /gfi-bot/frontend
# Build frontend
RUN npm ci --force
RUN npm run build

FROM caddy:2.5.1

EXPOSE 80
EXPOSE 443
# Copy caddy configration
COPY production/frontend.caddyfile /etc/caddy/Caddyfile
# Copy artifact
COPY --from=builder /gfi-bot/frontend/build /wwwroot