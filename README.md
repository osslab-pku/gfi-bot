# GFI-Bot

ML-powered 🤖 for finding and labeling good first issues in your GitHub project!

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

All modules interact with a MongoDB instance for both reading and writing data (except [`frontend`](frontend), which interact with backend using RESTful APIs). The MongoDB instance serves as a "single source of truth" and a way to decouple different modules. It will be used to store and continiously update issue statistics, training progress and performance, recommendation results, etc.

### Environment Setup

GFI-Bot uses [poetry](https://python-poetry.org/) for dependency management. Run the following commands with poetry to setup a working environment.

```shell script
poetry shell       # activate a working virtual environment
poetry install     # install all dependencies
pre-commit install # install pre-commit hooks
black .            # lint all Python code
pytest             # run all tests to confirm this environment is working
```

### Database Schema

TODO: Update documentation for MongoDB database schema.

## Deployment

TODO: Add explanations for how to maintain everything in our deployment server.
