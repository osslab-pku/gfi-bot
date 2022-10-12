### GFI-Bot Production Build

> **Notice: Do not make the docker image public after building.**


#### Production Setup Explained

we're using docker-compose to build a production instance of GFI-Bot, which consists of the following containers:

**mongo**: the database container, which stores all the data for GFI-Bot.

**frontend**: the frontend container, which builds and serves the frontend of GFI-Bot.

**gfi-bot**: the main container, which runs the fastAPI backend alongside the data retriever.

**gfi-trainer**: the training container, which trains the RecGFI model, updates predictions and performance metrics, and updates the database.


#### Initial Setup

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

Then, rename `example.env` to `.env` and set deployment configurations:

```ini
# MongoDB port (exposed to the host machine)
# NEVER expose MongoDB to the public internet
GFIBOT_MONGO_PORT=127.0.0.1:27020
# Backend port
GFIBOT_BACKEND_PORT=127.0.0.1:5000
# Frontend https / http port
GFIBOT_HTTPS_PORT=80
GFIBOT_HTTPS_PORT=443
GFIBOT_DATA_DIR=<path-to-gfi-data>
```

Finally, try executing

```bash
cd production/
./gfibot.sh up
```

to start your GFI-Bot service.

The current docker setup is battery-included, the caddy server serves the gfi-bot website and automatically renews the SSL certificate via [letsencrypt](https://letsencrypt.org/). You can also use your own SSL certificate by replacing the certificates in `certs/` with your own certificate files.


#### Updating GFI-Bot

To update GFI-Bot, you can simply run

```bash
cd production/
./gfibot.sh up
```