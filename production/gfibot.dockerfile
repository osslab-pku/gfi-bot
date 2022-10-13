# Dockerfile for the production environment
# ref: https://github.com/michaeloliverx/python-poetry-docker-example

FROM python:3.9 as python-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# `builder-base` stage is used to build deps + create our virtual environment
FROM python-base as builder-base
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        # deps for installing poetry
        curl \
        # deps for building python deps
        build-essential

# Install Poetry - respects $POETRY_VERSION & $POETRY_HOME
# Pin Poetry version: https://github.com/python-poetry/poetry/issues/6377
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/901bdf0491005f1b3db41947d0d938da6838ecb9/get-poetry.py | python -

# copy project requirement files here to ensure they will be cached.
WORKDIR $PYSETUP_PATH
COPY ./poetry.lock ./pyproject.toml ./
# install runtime deps - uses $POETRY_VIRTUALENVS_IN_PROJECT internally
RUN poetry install --no-dev

# `production` image used for runtime
FROM python-base as production
COPY --from=builder-base $VENV_PATH $VENV_PATH

COPY pyproject.toml /
COPY ./gfibot /gfibot
COPY ./production /production
EXPOSE 5000
WORKDIR /

RUN chmod +x production/run_production.sh
ENTRYPOINT production/run_production.sh $0 $@

CMD ["uvicorn", "gfibot.backend.server:app", "--host", "0.0.0.0", "--port", "5000"]
