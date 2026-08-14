# GFI-Bot Development & Deployment Guide

This document provides a comprehensive guide for developers and maintainers on understanding GFI-Bot's code structure, database schemas, testing procedures, and local or production deployment workflows.

---

## Table of Contents

- [1. Project Architecture & Code Structure](#1-project-architecture--code-structure)
- [2. Database Schemas & Collections](#2-database-schemas--collections)
- [3. Testing & Code Quality](#3-testing--code-quality)
- [4. Local & Production Deployment Guide](#4-local--production-deployment-guide)
  - [4.1 Prerequisites & Virtual Environment](#41-prerequisites--virtual-environment)
  - [4.2 Lightweight Local Setup](#42-lightweight-local-setup)
  - [4.3 Data Collection & Dataset Preparation](#43-data-collection--dataset-preparation)
  - [4.4 Model Training & Prediction](#44-model-training--prediction)
  - [4.5 Running the Backend Server](#45-running-the-backend-server)
  - [4.6 Production Docker Setup](#46-production-docker-setup)

---

## 1. Project Architecture & Code Structure

GFI-Bot is organized into four main operational modules, decoupled by a central MongoDB instance:

1. **[`gfibot.data`](gfibot/data)**: Modules to periodically and incrementally collect repository metadata, commits, issues, pull requests, and contributor activity from GitHub API.
2. **[`gfibot.model`](gfibot/model)**: Machine learning recommendation engine (RecGFI) that processes collected issue statistics, builds training datasets, evaluates model performance across algorithms (RandomForest, GradientBoosting, LogisticRegression, SVM, MLP), and computes GFI probability scores.
3. **[`gfibot.backend`](gfibot/backend)**: RESTful API server built on FastAPI and Uvicorn. Exposes API routes (`/api/repos`, `/api/issue`, `/api/github`, `/api/user`, `/api/model`, `/api/chatbot`) for the frontend portal and GitHub App webhooks.
4. **[`frontend`](frontend)**: The web interface for browsing project health metrics, discovering recommended Good First Issues, inspecting model evaluation stats, and interacting with the Help Chatbot.

```
gfi-bot/
├── gfibot/
│   ├── backend/        # FastAPI REST API routes & background task schedulers
│   ├── collections/    # MongoEngine ORM database schema definitions
│   ├── data/           # GitHub API scrapers & dataset builders
│   └── model/          # RecGFI ML models, predictors & systematic evaluation
├── frontend/           # Web portal frontend application
├── production/         # Docker Compose & deployment configurations
├── tests/              # Pytest test suites (backend, data, model)
├── DEVELOPMENT.md      # Development & deployment guide
├── USE_CASES.md        # System specifications & use cases
└── pyproject.toml      # Dependency management & project configuration
```

---

## 2. Database Schemas & Collections

MongoDB serves as the single source of truth for GFI-Bot. All collection schemas are formally defined as Python classes using [MongoEngine](http://mongoengine.org/) inside [`gfibot.collections`](gfibot/collections):

- **[`gfibot.collections.data`](gfibot/collections/data.py)**:
  - `Repo`: Repository metadata (stars, language, topics, monthly activity statistics).
  - `RepoIssue`: Detailed issue metadata (title, body, labels, state, timestamps, readability indices).
  - `RepoCommit`: Commit logs, author/committer information.
  - `ResolvedIssue`: Resolved issues and newcomer resolution commit counts.
  - `User`: Global GitHub user contribution histories.
- **[`gfibot.collections.model`](gfibot/collections/model.py)**:
  - `Prediction`: Model-predicted GFI probability scores for open issues.
  - `TrainingSummary`: Model classification performance (AUC, accuracy, F1) per repository.
  - `ModelEvaluation`: Systematic evaluation results (alternative model comparisons, ablation studies, feature importances).
- **[`gfibot.collections.backend`](gfibot/collections/backend.py)**:
  - `GfiUsers`: Registered web portal users and token donations.
  - `GfiQueries`: Registered repositories and update configurations.
  - `ChatbotSession`: Help chatbot session memory and Q&A history.
- **[`gfibot.collections.log`](gfibot/collections/log.py)**:
  - Task execution logs and exception records.

---

## 3. Testing & Code Quality

### Running Unit Tests

GFI-Bot uses `pytest` and `mongomock` for fast, isolated unit testing without modifying the production database.

```bash
# Activate Poetry virtual environment
poetry shell

# Run all test suites
pytest

# Run a specific backend or model test file
pytest tests/backend/test_issue.py
pytest tests/model/test_evaluation.py
```

### Code Style & Pre-Commit

We enforce PEP 8 formatting with `black` and manage pre-commit hooks:

```bash
# Lint code formatting with Black
black .

# Install pre-commit hooks
pre-commit install
```

---

## 4. Local & Production Deployment Guide

### 4.1 Prerequisites & Virtual Environment

- Python 3.9+
- MongoDB 4.2+ (Local or Docker instance)
- Poetry (`pip install poetry`)

Initialize the environment:

```bash
poetry shell
poetry install
```

### 4.2 Lightweight Local Setup

For quick local testing without scanning thousands of GitHub projects:

1. Configure MongoDB connection URL in `pyproject.toml` or set environment variable:
   ```toml
   [tool.gfibot.mongodb]
   url = "mongodb://localhost:27017"
   db = "gfibot_dev"
   ```
2. Create `tokens.txt` in the root folder containing at least one GitHub Personal Access Token (PAT):
   ```text
   ghp_yourGitHubPersonalAccessToken123
   ```
3. Test your token setup:
   ```bash
   python -m gfibot.check_tokens
   ```

### 4.3 Data Collection & Dataset Preparation

Run background data ingestion for configured repositories:

```bash
# Collect historical data (use --nprocess to adjust concurrency)
python -m gfibot.data.update --nprocess=2

# Build training dataset
python -m gfibot.data.dataset --since=2022.01.01 --nprocess=2
```

### 4.4 Model Training & Prediction

Train the RecGFI recommendation models and generate GFI predictions for open issues:

```bash
# Train predictor models
python -m gfibot.model.predictor
```

### 4.5 Running the Backend Server

Launch the FastAPI uvicorn server locally:

```bash
python -m gfibot.backend.server --port 8234 --reload
```

The REST API will be available at `http://127.0.0.1:8234` with interactive OpenAPI docs at `http://127.0.0.1:8234/docs`.

### 4.6 Production Docker Setup

We provide production docker scripts in the `production/` folder:

```bash
cd production
docker-compose up -d --build
```
