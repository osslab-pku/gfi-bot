FROM node:16

EXPOSE 80
EXPOSE 443

# Install caddy
RUN apt install -y debian-keyring debian-archive-keyring apt-transport-https
RUN curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
RUN curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
RUN apt update
RUN apt install caddy

WORKDIR /
COPY ./ /gfi-bot/
WORKDIR /gfi-bot/frontend
RUN npm install --force
RUN npm run build:prod

WORKDIR /gfi-bot/
RUN caddy run --config=/gfibot/production/Caddyfile
