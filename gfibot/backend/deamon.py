import argparse
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import random

from gfibot.data.update import update_repo
from gfibot.collections import *
from gfibot.check_tokens import check_tokens
from gfibot.data.dataset import get_dataset_all
from gfibot.model.predictor import update_training_summary, update_prediction

from gfibot import CONFIG, TOKENS

logger = logging.getLogger(__name__)

DEFAULT_JOB_ID = "gfi_demon"


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(demon, "cron", hour=0, minute=0, id=DEFAULT_JOB_ID)
    for query in GfiQueries.objects():
        if query.update_config:
            task_id = query.update_config.task_id
            interval = query.update_config.interval
            tokens = [user.github_access_token for user in GfiUsers.objects()]
            valid_tokens = list(set(tokens) - check_tokens(tokens))
            scheduler.add_job(
                update_repo,
                "interval",
                args=[random.choice(valid_tokens), query.owner, query.name],
                seconds=interval,
                next_run_time=datetime.utcnow(),
                id=task_id,
            )
            """update query begin time"""
            query.update_config.begin_time = datetime.utcnow()
            query.update_config.save()
            logger.info("Scheduled task: " + task_id + " added.")
    scheduler.start()
    logger.info("Scheduler started.")
    return scheduler


def demon(init=False):
    logger.info("Demon started. at " + str(datetime.now()))

    if not init:
        avaliable_tokens = [user.github_access_token for user in GfiUsers.objects()]
        failed_tokens = check_tokens(avaliable_tokens)
        valid_tokens = list(set(avaliable_tokens) - failed_tokens)
        for i, repo in enumerate(Repo.objects()):
            update_config = (
                GfiQueries.objects(Q(repo=repo.name) & Q(owner=repo.owner))
                .first()
                .update_config
            )
            if not update_config:
                update_repo(
                    valid_tokens[i % len(avaliable_tokens)], repo.owner, repo.name
                )
    else:
        failed_tokens = check_tokens(TOKENS)
        valid_tokens = list(set(TOKENS) - failed_tokens)
        for i, project in enumerate(CONFIG["gfibot"]["projects"]):
            owner, name = project.split("/")
            update_repo(valid_tokens[i % len(valid_tokens)], owner, name)

    get_dataset_all("2008.01.01")

    for threshold in [1, 2, 3, 4, 5]:
        logger.info(
            "Update TrainingSummary and Prediction for threshold "
            + str(threshold)
            + "."
        )
        update_training_summary(threshold)
        update_prediction(threshold)


def initialize():
    logger.info("Initializing...")
    demon(init=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true", default=False)
    should_init = parser.parse_args().init
    if should_init:
        initialize()
