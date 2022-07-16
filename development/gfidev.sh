#!/bin/bash
set -e

# load .env if it exists
if [ -f .env ]; then
    set -o allexport
    source .env
    set +o allexport
fi

export COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-"gfidev_$(whoami)"}
export GFIBOT_DATA_DIR=${GFIBOT_DATA_DIR:-"~/gfi-data/"}
export COMPOSE_COMMAND="$([[ -w /var/run/docker.sock ]] && echo '' || echo 'sudo ')docker-compose"
export SCREEN_NAME_VITE="${COMPOSE_PROJECT_NAME}_vite"
export SCREEN_NAME_BACKEND="${COMPOSE_PROJECT_NAME}_backend"

up(){
    # check data folder
    [[ -d "$GFIBOT_DATA_DIR" ]] || mkdir -p "$GFIBOT_DATA_DIR"
    [[ -d "$GFIBOT_DATA_DIR" ]] || { echo "Could not create data directory $GFIBOT_DATA_DIR"; exit 1; }

    # check env vars
    for var in GFIBOT_DATA_DIR GFIBOT_MONGO_PORT GFIBOT_BACKEND_PORT GFIBOT_FRONTEND_PORT GFIBOT_HTTPS_PORT GFIBOT_HTTP_PORT; do
        [[ -n "${!var}" ]] || { echo "Missing env var $var"; exit 1; }
        echo "$var=${!var}"
    done
    echo "[${COMPOSE_PROJECT_NAME}] Creating services..."
    ${COMPOSE_COMMAND} up -d --build

    echo "[${COMPOSE_PROJECT_NAME}] Starting backend..."
    if screen -list | grep -q "$SCREEN_NAME_BACKEND"; then
        screen -S "$SCREEN_NAME_BACKEND" -X quit
    fi
    screen -dmS "$SCREEN_NAME_BACKEND" bash -c "cd ../ && poetry run python3 -m gfibot.backend.server --host 0.0.0.0 --port ${GFIBOT_BACKEND_PORT} --reload"

    echo "[${COMPOSE_PROJECT_NAME}] Starting vite..."
    if screen -list | grep -q "$SCREEN_NAME_VITE"; then
        screen -S "$SCREEN_NAME_VITE" -X quit
    fi
    screen -dmS "$SCREEN_NAME_VITE" bash -c "cd ../frontend && npm ci && npx vite dev --host --port ${GFIBOT_FRONTEND_PORT}"
}

reload(){
    echo "[${COMPOSE_PROJECT_NAME}] Recreating containers..."
    ${COMPOSE_COMMAND} up -d --force-recreate --no-build
    echo "[${COMPOSE_PROJECT_NAME}] Restarting backend..."
    if screen -list | grep -q "$SCREEN_NAME_BACKEND"; then
        screen -S "$SCREEN_NAME_BACKEND" -X quit
    fi
    echo "[${COMPOSE_PROJECT_NAME}] Restarting vite..."
    if screen -list | grep -q "$SCREEN_NAME_VITE"; then
        screen -S "$SCREEN_NAME_VITE" -X quit
    fi
}

down(){
    echo "[${COMPOSE_PROJECT_NAME}] Stopping containers..."
    ${COMPOSE_COMMAND} down

    echo "[${COMPOSE_PROJECT_NAME}] Stopping vite..."
    screen -X -S "$SCREEN_NAME_VITE" quit

    echo "[${COMPOSE_PROJECT_NAME}] Stopping backend..."
    screen -X -S "$SCREEN_NAME_BACKEND" quit
}

logs(){
    ${COMPOSE_COMMAND} logs ${1:-}
}

usage(){
    echo "Usage: $0 [up|reload|down|logs]
    up:     Create and start containers
    reload: Recreate containers
    down:   Stop containers
    logs:   Show logs of containers"
    exit 2;
}

# argparse
case "$1" in
    up)
        up
        ;;
    reload)
        reload
        ;;
    down)
        down
        ;;
    logs)
        logs "$2"
        ;;
    *)
        usage
        ;;
esac