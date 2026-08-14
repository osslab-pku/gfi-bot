import argparse
import logging
import os

import uvicorn
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
import mongoengine

from gfibot import CONFIG
from gfibot.backend.routes import github, issue, repos, user, model, chatbot
from gfibot.backend.scheduled_tasks import start_scheduler

app = FastAPI()

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
app = FastAPI(title="GFI-Bot")

app.include_router(repos.api, prefix="/api/repos")
app.include_router(issue.api, prefix="/api/issue")
app.include_router(github.api, prefix="/api/github")
app.include_router(user.api, prefix="/api/user")
app.include_router(model.api, prefix="/api/model")
app.include_router(chatbot.api, prefix="/api/chatbot")



def get_scheduler() -> BackgroundScheduler:
    scheduler = getattr(app, "scheduler", None)
    if scheduler is None:
        app.scheduler = start_scheduler()
        return app.scheduler
    return scheduler


def get_db_connection():
    db_connection = getattr(app, "db_connection", None)
    if db_connection is None:
        app.db_connection = mongoengine.connect(
            CONFIG["mongodb"]["db"],
            host=CONFIG["mongodb"]["url"],
            tz_aware=True,
            uuidRepresentation="standard",
            connect=False,
        )
        return app.db_connection
    return db_connection


@app.on_event("startup")
def startup_event():
    get_db_connection()
    _skip_scheduler = os.environ.get("GFIBOT_SKIP_SCHEDULER", False)
    if not _skip_scheduler:
        get_scheduler()
    else:
        logger.info("Skipping scheduler")


if __name__ == "__main__":
    parser = argparse.ArgumentParser("GFI-Bot Backend (FastAPI)")
    parser.add_argument("-p", "--port", default=8234, type=int, help="Port to run on")
    parser.add_argument("-o", "--host", default="127.0.0.1", help="Host to run on")
    parser.add_argument(
        "-r",
        "--reload",
        action="store_true",
        default=False,
        help="Reload on code changes",
    )
    args = parser.parse_args()
    logger.info("Starting uvicorn server on port %d", args.port)

    uvicorn.run(
        "gfibot.backend.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
