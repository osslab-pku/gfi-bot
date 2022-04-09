# GFI-Bot

![Python Lint](https://github.com/osslab-pku/gfi-bot/actions/workflows/python-lint.yml/badge.svg)
![GFI-Bot Tests](https://github.com/osslab-pku/gfi-bot/actions/workflows/test-gfi-bot.yml/badge.svg)
![GFI-Bot Coverage](https://img.shields.io/codecov/c/github/osslab-pku/gfi-bot?label=GFI-Bot%20Coverage)
![License](https://img.shields.io/github/license/osslab-pku/gfi-bot?label=License)

ML-powered 🤖 for finding and labeling good first issues in your GitHub project!

The tool is based on the following paper:
W. Xiao, H. He, W. Xu, X. Tan, J. Dong, M. Zhou. Recommending Good First Issues in GitHub OSS Projects. Accepted at [ICSE'2022](https://conf.researchr.org/home/icse-2022).

## Get Started

TODO: Add a quick usage guide after a prototype is finished.

## Development

### Project Organization

GFI-Bot is organized into five main modules:

1. [`gfibot.data`](gfibot/data): Modules to periodically and incrementally collect latest issue statistics on registered GitHub projects.
2. [`gfibot.model`](gfibot/data): Modules to periodically train GFI recommendation models based on issue statistics collected by [`gfibot.data`](gfibot/data).
3. [`gfibot.backend`](gfibot/backend): Modules to provide RESTful APIs for interaction with [`frontend`](frontend).
4. [`frontend`](frontend): A standalone JavaScript (or TypeScript?) project as our website. This website will be used both as the main portal of GFI-Bot and as a control panel for users to find recommended good first issues or track bot status for their projects.
5. [`github-app`](github-app): A standalone JavaScript (or TypeScript?) project for interacting with GitHub.

All modules interact with a MongoDB instance for both reading and writing data (except [`frontend`](frontend), which interact with backend using RESTful APIs). The MongoDB instance serves as a "single source of truth" and the main way to decouple different modules. It will be used to store and continiously update issue statistics, training progress and performance, recommendation results, etc.

### Environment Setup

GFI-Bot uses [poetry](https://python-poetry.org/) for dependency management. Run the following commands with poetry to setup a working environment.

```shell script
poetry shell       # activate a working virtual environment
poetry install     # install all dependencies
pre-commit install # install pre-commit hooks
black .            # lint all Python code
pytest             # run all tests to confirm this environment is working
```

Then, configure a MongoDB instance (4.2 or later) and specify its connection URL in [`pyproject.toml`](pyproject.toml).

### Database Schemas

As mentioned before, the MongoDB instance serves as a "single source of truth" and decouples different modules. Therefore, before you start working with any part of GFI-Bot, it is important to know how the data look like in the MongoDB. For this purpose, we adopt [mongoengine](http://mongoengine.org/) as an ORM-alike layer to formally describe and enforce schemas for each MongoDB collection and all collections are defined as Python classes [here](gfibot/collections.py).

### Development Guidelines

Contributions should follow existing conventions and styles in the codebase with best effort. All commit messages should follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification.

## Deployment

First, determine some GitHub projects of interest and specify them in [`pyproject.toml`](pyproject.toml). Configure a list of GitHub access tokens (line separated) in `tokens.txt`. Make sure to use more tokens in order to quickly bootstrap GFI-Bot. Run the following script to check if the tokens are configured correctly.

```shell script
python -m gfibot.check_tokens
```

Next, run the following script to collect historical data for the interested projects. This can take some time (up to days) to finish for the first run, but can perform quick incremental update on an existing database. This script should be done periodically (e.g., as a scheduled background task) to ensure that the MongoDB database reflect the latest state in the specified repositories.

```shell script
python -m gfibot.data.update
```
