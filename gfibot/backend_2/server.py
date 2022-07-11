import argparse
import logging
import os

import uvicorn
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
import mongoengine

from gfibot import CONFIG
from .routes import github, issue, repos, user, model
from .scheduled_tasks import start_scheduler

app = FastAPI()

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
app = FastAPI(title='GFI-Bot')

app.include_router(repos.api, prefix='/api/repos')
app.include_router(issue.api, prefix='/api/issue')
app.include_router(github.api, prefix='/api/github')
app.include_router(user.api, prefix='/api/user')
app.include_router(model.api, prefix='/api/model')


def get_scheduler() -> BackgroundScheduler:
    try:
        return app.scheduler
    except AttributeError:
        app.scheduler = start_scheduler()
        return app.scheduler

def get_db_connection():
    try:
        return app.db_connection
    except AttributeError:
        app.db_connection = mongoengine.connect(
            CONFIG["mongodb"]["db"],
            host=CONFIG["mongodb"]["url"],
            tz_aware=True,
            uuidRepresentation="standard",
            connect=False,
        )
        return app.db_connection


@app.on_event('startup')
def startup_event():
    get_db_connection()
    _skip_scheduler = os.environ.get('GFIBOT_SKIP_SCHEDULER', False)
    if not _skip_scheduler:
        get_scheduler()
    else:
        logger.info("Skipping scheduler")
        app.scheduler = None


if __name__ == '__main__':
    parser = argparse.ArgumentParser('GFI-Bot Backend (FastAPI)')
    parser.add_argument('-p', '--port', default=8234, type=int, help='Port to run on')
    parser.add_argument('-o', '--host', default='127.0.0.1', help='Host to run on')
    parser.add_argument('-r', '--reload', action="store_true", default=False, help='Reload on code changes')
    args = parser.parse_args()
    logger.info('Starting uvicorn server on port %d', args.port)

    uvicorn.run(
        'gfibot.backend_2.server:app',
        host=args.host,
        port=args.port,
        reload=args.reload,
    )