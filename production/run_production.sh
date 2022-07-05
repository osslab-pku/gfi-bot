#!/bin/bash

set -e

# activate our virtual environment here
. /opt/pysetup/.venv/bin/activate

sed -i 's/localhost/mongodb/g' ./pyproject.toml
python3 production/set_tokens_private_production.py

exec "$@"