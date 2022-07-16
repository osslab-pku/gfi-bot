FROM node:16 AS builder

# install dependencies
RUN mkdir /gfi-bot/ /gfi-bot/frontend
COPY ./frontend/package-lock.json ./frontend/package.json /gfi-bot/frontend/
WORKDIR /gfi-bot/frontend
RUN npm ci --force

# Build frontend
ARG NODE_ENV
ARG REACT_APP_BASE_URL
COPY ./frontend/ /gfi-bot/frontend
RUN npm run build

FROM caddy:2.5.1

EXPOSE 80
EXPOSE 443
# Copy caddy configration
COPY production/frontend.caddyfile /etc/caddy/Caddyfile
# Copy artifact
COPY --from=builder /gfi-bot/frontend/build /wwwroot