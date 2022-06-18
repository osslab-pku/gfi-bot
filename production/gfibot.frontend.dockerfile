FROM node:16
ENV NODE_ENV=production

WORKDIR /
COPY ./ /gfi-bot
WORKDIR /gfi-bot/frontend
RUN npm ci --force
RUN npm run build:prod

FROM caddy:2.5.1

EXPOSE 80
EXPOSE 443
WORKDIR /gfi-bot
RUN caddy run --config=production/Caddyfile
