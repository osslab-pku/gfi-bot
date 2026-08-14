# GFI-Bot

![Python Lint](https://github.com/osslab-pku/gfi-bot/actions/workflows/python-lint.yml/badge.svg)
![GFI-Bot Tests](https://github.com/osslab-pku/gfi-bot/actions/workflows/test-gfi-bot.yml/badge.svg)
![GFI-Bot Coverage](https://img.shields.io/codecov/c/github/osslab-pku/gfi-bot?label=GFI-Bot%20Coverage)
![License](https://img.shields.io/github/license/osslab-pku/gfi-bot?label=License)
[![GFI-Bot](https://gfibot.io/api/repos/badge?owner=osslab-pku&name=gfi-bot)](https://gfibot.io/?owner=osslab-pku&name=gfi-bot)

ML-powered 🤖 for finding and labeling good first issues in your GitHub project!

A GFI-Bot introduction paper is available as follows (in [ESEC/FSE 2022 Demonstration Track](https://2022.esec-fse.org/track/fse-2022-demonstrations)):

* Hao He, Haonan Su, Wenxin Xiao, Runzhi He, and Minghui Zhou. 2022. GFI-Bot: Automated Good First Issue Recommendation on GitHub. In Proceedings of the 2022 ACM 30th Joint European Software Engineering Conference and Symposium on the Foundations of Software Engineering, ESEC/FSE 2022, Singapore, November 14-16, 2022. ACM. https://hehao98.github.io/files/2022-gfibot.pdf

The underlying ML approach is introduced in the following paper:

* Wenxin Xiao, Hao He, Weiwei Xu, Xin Tan, Jinhao Dong, and Minghui Zhou. 2022. Recommending Good First Issues in GitHub OSS Projects. In Proceedings of the 44th International Conference on Software Engineering, ICSE 2022, Pittsburgh, PA, USA, May 21–29, 2022. ACM. https://hehao98.github.io/files/2022-recgfi.pdf

See [CITATIONS.bib](CITATIONS.bib) for the BibTeX citations. We also provide an offline good first issue recommendation dataset at [Zenodo](https://doi.org/10.5281/zenodo.6665931).

## About the Logo

The GFI-Bot logo and mascot (designed by Haonan Su) symbolizes the growth and onboarding of open-source software (OSS) newcomers:
* **The Sprouting Plant 🌱**: Represents beginner developers planting their first contribution seed and growing into core open-source maintainers.
* **The Helper Robot 🤖**: Represents GFI-Bot's automated Machine Learning recommendation engine (RecGFI), helping project maintainers effortlessly identify and label Good First Issues (GFIs).


## Get Started

GFI-Bot is available at https://gfibot.io, where you can browse through existing good first issue recommendations or register your own repository for recommendation. GFI-Bot can be installed in GitHub repositories from [the GitHub App page](https://github.com/apps/GFI-Bot).

**NOTE: GFI-Bot is currently in pre-alpha stage. It is undergoing rapid development and still highly unstable. We cannot guanrantee the preseveration of registered users and repositories in the next release and it may have unexpected behaviors on GitHub. We will change this note after GFI-Bot reaches a certain level of maturity**

## Roadmap

We describe our envisioned use cases for GFI-Bot in this [documentation](USE_CASES.md).

Currently, we are focusing on the following tasks:
1. Identifying an optimal training strategy
2. Improving user experience

## Development & Deployment

For a detailed guide on project architecture, database schemas, running unit tests, lightweight local setup, and production deployment, please refer to our comprehensive **[DEVELOPMENT.md](DEVELOPMENT.md)** guide.

Then, configure a MongoDB instance (4.2 or later) and specify its connection URL in [`pyproject.toml`](pyproject.toml).

### Database Schemas

As mentioned before, the MongoDB instance serves as a "single source of truth" and decouples different modules. Therefore, before you start working with any part of GFI-Bot, it is important to know how the data look like in the MongoDB. For this purpose, we adopt [mongoengine](http://mongoengine.org/) as an ORM-alike layer to formally describe and enforce schemas for each MongoDB collection and all collections are defined as Python classes [here](gfibot/collections).

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
