### GFI-Bot Development Setup

> **The dev setup is pretty alpha-stage, it's only tested on the production machine (Ubuntu 20.04) with one user.**

#### Development Setup Explained

`gfidev.sh` starts a MongoDB instance `gfidev_xxx_mongo`, a caddy webserver, and 2 screen sessions:

**gfidev_xxx_vite** runs a vite dev server (with hmr, the dev frontend refreshes within 1 sec on code changes)

**gfidev_xxx_backend** runs a FastAPI backend (automatically reloads on backend code changes; to avoid wasting rate limits, the background scheduler is disabled by default)

#### Initial Setup

##### Building the dataset

The most effortless way to build the dev dataset is to copy it from the production server. (stop the production database before copying)

```bash
cp -r <path-to-gfi-data> <path-to-gfi-data-alt>
```

Alternatively, you may build the dataset from scratch. (this will take a while)

```bash
GFIBOT_ENV=dev python3 -m gfibot.backend.scheduled_tasks --init
```

##### Starting the dev setup

First, rename `example.env` to `.env` and set deployment configurations:

**Note each GFI-Bot instance needs unique ports and a unique GFIBOT_DATA_DIR to avoid conflicts.**

```ini
# MongoDB port (exposed to the host machine)
GFIBOT_MONGO_PORT=127.0.0.1:27021  # <- check pyproject.toml
# Backend port
GFIBOT_BACKEND_PORT=127.0.0.1:8123
# Frontend https / http port
GFIBOT_HTTPS_PORT=80
GFIBOT_HTTPS_PORT=443
GFIBOT_DATA_DIR=<path-to-gfi-data-alt>
```

Then, run the dev setup:

```bash
cd development/
./gfidev.sh up
```
