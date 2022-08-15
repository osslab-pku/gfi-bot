# GFI-Bot

![Python Lint](https://github.com/osslab-pku/gfi-bot/actions/workflows/python-lint.yml/badge.svg)
![GFI-Bot Tests](https://github.com/osslab-pku/gfi-bot/actions/workflows/test-gfi-bot.yml/badge.svg)
![GFI-Bot Coverage](https://img.shields.io/codecov/c/github/osslab-pku/gfi-bot?label=GFI-Bot%20Coverage)
![License](https://img.shields.io/github/license/osslab-pku/gfi-bot?label=License)
[![GFI-Bot](https://gfibot.io/api/repo/badge?owner=osslab-pku&name=gfi-bot)](https://gfibot.io/?owner=osslab-pku&name=gfi-bot)

ML-powered 🤖 for finding and labeling good first issues in your GitHub project!

A GFI-Bot introduction paper is available as follows (submitted to [ESEC/FSE 2022 Demonstration Track](https://2022.esec-fse.org/track/fse-2022-demonstrations)):

* Hao He, Haonan Su, Wenxin Xiao, Runzhi He, and Minghui Zhou. 2022. GFI-Bot: Automated Good First Issue Recommendation on GitHub. Currently Under Review at the ESEC/FSE 2022 Demonstration Track. https://hehao98.github.io/files/2022-gfibot.pdf

The underlying ML approach is introduced in the following paper:

* Wenxin Xiao, Hao He, Weiwei Xu, Xin Tan, Jinhao Dong, and Minghui Zhou. 2022. Recommending Good First Issues in GitHub OSS Projects. In Proceedings of the 44th International Conference on Software Engineering, ICSE 2022, Pittsburgh, PA, USA, May 21–29, 2022. ACM. https://hehao98.github.io/files/2022-recgfi.pdf

We provide a good first issue recommendation dataset at [Zenodo](https://doi.org/10.5281/zenodo.6665931).

## Get Started

GFI-Bot is available at https://gfibot.io, where you can browse through existing good first issue recommendations or register your own repository for recommendation. GFI-Bot can be installed in GitHub repositories from [the GitHub App page](https://github.com/apps/GFI-Bot).

**NOTE: GFI-Bot is currently in pre-alpha stage. It is undergoing rapid development and still highly unstable. We cannot guanrantee the preseveration of registered users and repositories in the next release and it may have unexpected behaviors on GitHub. We will change this note after GFI-Bot reaches a certain level of maturity**

## Roadmap

We describe our envisioned use cases for GFI-Bot in this [documentation](USE_CASES.md).

Currently, we are focusing on the following tasks:
1. Identifying an optimal training strategy
2. Improving user experience

## Development

### Project Organization

GFI-Bot is organized into four main modules:

1. [`gfibot.data`](gfibot/data): Modules to periodically and incrementally collect latest issue statistics on registered GitHub projects.
2. [`gfibot.model`](gfibot/data): Modules to periodically train GFI recommendation models based on issue statistics collected by [`gfibot.data`](gfibot/data).
3. [`gfibot.backend`](gfibot/backend): Modules to provide RESTful APIs for interaction with [`frontend`](frontend) and the GitHub App.
4. [`frontend`](frontend): A standalone JavaScript (or TypeScript?) project as our website. This website will be used both as the main portal of GFI-Bot and as a control panel for users to find recommended good first issues or track bot status for their projects.

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

Contributions should follow existing conventions and styles in the codebase with best effort. Please add type annotations for all class members, function parameters, and return values. When writing commit messages, please follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification.

## Deployment

First, determine some GitHub projects of interest and specify them in [`pyproject.toml`](pyproject.toml). Configure a list of GitHub access tokens (line separated) in `tokens.txt`. Make sure to use more tokens in order to quickly bootstrap GFI-Bot. Run the following script to check if the tokens are configured correctly.

```shell script
python -m gfibot.check_tokens
```

We provide scripts for building docker images in the `production/` folder. You can choose to build docker images to quickly setup MongoDB and backend by following the README there.

### Dataset Preparation

Next, run the following script to collect historical data for the interested projects. This can take some time (up to days) to finish for the first run, but can perform quick incremental update on an existing database. This script should be done periodically (e.g., as a scheduled background task) to ensure that the MongoDB database reflect the latest state in the specified repositories.

```shell script
python -m gfibot.data.update --nprocess=4 # you can increase parallelism with more GitHub tokens
```

Then, build a dataset for training and prediction as follows. This script may also take a long time but can be accelerated with more processes.

```shell script
python -m gfibot.data.dataset --since=2008.01.01 --nprocess=4
```

### Model Training

Model training can be simply done by running the following script.

```shell script
python -m gfibot.model.predictor
```

### Dataset Dump

The Zenodo dataset can be dumped using the following script. See [Zenodo](https://doi.org/10.5281/zenodo.6665931) for more details about how to use the dumped dataset.

```shell script
mongodump --uri=mongodb://localhost:27020 --db=gfibot --collection=dataset --query="{\"resolver_commit_num\":{\"\$ne\":-1}}" --gzip
mongodump --uri=mongodb://localhost:27020 --db=gfibot --collection=resolved_issue --query="{\"resolver_commit_num\":{\"\$ne\":-1}}" --gzip
```
