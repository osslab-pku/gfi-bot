### GFI-Bot Production Build

> **Notice: Do not make the docker image public after building.**

**Preliminary**, we're using docker-compose to build a production instance of GFI-Bot, which includes a Flask backend, a Mongo database, RecGFI  and data retrieving modules.

You should initially create a `production_secrets.json` file in this directory in order to register your GitHub APP id and secrets, as well as information of a g-mail account (if you want to send emails to users). The file should be laid out as below:

```json
{
    "web_client": {
        "id": "$web_client_id",
        "secret": "$web_client_secret"
    },
    "git_app": {
        "id": "$github_app_id",
        "secret": "$github_app_secret"
    },
    "mail": {
        "email": "$gmail_address",
        "password": "$gmail_service_password"
    }
}
```

Then, try executing

```bash
cd production
docker-compose build
docker-compose up
```

to start your GFI-Bot service.

The docker image been built doesn't consist a web server, so it's up to you to choose which kind of web server to use. Currently, we're using [caddy](https://caddyserver.com/) as our web server. A Caddy file as below would be capable for development environment: 

```
$your_web_domain {
    route {
        reverse_proxy /api/* $your_server_url {
            header_down +Access-Control-Allow-Origin "*"
            header_down +Access-Control-Allow-Methods "OPTIONS, DELETE, GET, HEAD, POST, PUT"
        }
        root * $frontend_builds_location
        try_files {path} /index.html
        file_server
    }
}
```