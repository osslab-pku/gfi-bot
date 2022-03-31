#!/bin/bash

python3 set_tokens_private.py

source $HOME/.poetry/env
export FLASK_APP=gfi_backend
export FLASK_ENV=development
flask run --host=0.0.0.0