import argparse
import mongoengine
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import random
import datetime

from gfibot.data.update import update_repo
from gfibot.collections import *
from gfibot.check_tokens import check_tokens
from gfibot.data.dataset import get_dataset_for_repo, get_dataset_all
from gfibot.model.predictor import (
    update_training_summary,
    update_prediction,
    update_repo_prediction,
)
from gfibot.backend.utils import (
    send_email,
    executor,
    add_comment_to_github_issue,
    add_gfi_label_to_github_issue,
)

from gfibot import CONFIG, TOKENS

logger = logging.getLogger(__name__)

DEFAULT_JOB_ID = "gfi_daemon"


def tag_and_comment(github_login, owner, name):
    repo_query = GfiQueries.objects(Q(name=name) & Q(owner=owner)).first()
    threshold = repo_query.repo_config.gfi_threshold
    newcomer_threshold = repo_query.repo_config.newcomer_threshold
    issue_tag = repo_query.repo_config.issue_tag
    if repo_query and repo_query.is_github_app_repo:
        predicts = Prediction.objects(
            Q(owner=owner)
            & Q(name=name)
            & Q(probability__gte=threshold)
            & Q(threshold=newcomer_threshold)
        )
        should_comment = repo_query.repo_config.need_comment
        for predict in predicts:
            if predict.tagged != True:
                if (
                    add_gfi_label_to_github_issue(
                        github_login=github_login,
                        repo_name=predict.name,
                        repo_owner=predict.owner,
                        issue_number=predict.number,
                        label_name=issue_tag,
                    )
                    == 200
                ):
                    predict.tagged = True
                    predict.save()
            if predict.commented != True and should_comment:
                comment = "[GFI-Bot] Predicted as Good First Issue with probability {}%.".format(
                    round((predict.probability) * 100, 2)
                )
                if (
                    add_comment_to_github_issue(
                        github_login=github_login,
                        repo_name=predict.name,
                        repo_owner=predict.owner,
                        issue_number=predict.number,
                        comment=comment,
                    )
                    == 200
                ):
                    predict.commented = True
                    predict.save()


def update_gfi_info(token: str, owner: str, name: str):
    logger.info(
        "Updating gfi info for " + owner + "/" + name + " at {}.".format(datetime.now())
    )
    update_repo(token, owner, name)
    begin_time = "2008.01.01"
    begin_datetime = datetime.strptime(begin_time, "%Y.%m.%d")
    get_dataset_for_repo(owner=owner, name=name, since=begin_datetime)
    update_repo_prediction(owner, name)
    user_github_login = None
    query = GfiQueries.objects(Q(name=name) & Q(owner=owner)).first()
    if query.is_github_app_repo and query.app_user_github_login:
        user_github_login = query.app_user_github_login
    if user_github_login:
        executor.submit(tag_and_comment, user_github_login, owner, name)
    logger.info(
        "Update gfi info for "
        + owner
        + "/"
        + name
        + " done at {}.".format(datetime.now())
    )
    if user_github_login:
        send_email(
            user_github_login,
            "[GFI-Bot] update finished",
            "GFI updated for " + owner + "/" + name + " done.",
        )


def update_gfi_update_job(scheduler, job_id, name, owner):
    query = GfiQueries.objects(Q(name=name) & Q(owner=owner)).first()
    if query:
        interval = query.update_config.interval
        tokens = [user.github_access_token for user in GfiUsers.objects()]
        valid_tokens = list(set(tokens) - check_tokens(tokens))
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        scheduler.add_job(
            update_gfi_info,
            "interval",
            seconds=interval,
            next_run_time=datetime.utcnow(),
            id=job_id,
            args=[random.choice(valid_tokens), query.owner, query.name],
        )


def start_scheduler():
    mongoengine.connect(
        CONFIG["mongodb"]["db"],
        host=CONFIG["mongodb"]["url"],
        tz_aware=True,
        uuidRepresentation="standard",
    )

    scheduler = BackgroundScheduler()
    scheduler.add_job(daemon, "cron", hour=0, minute=0, id=DEFAULT_JOB_ID)
    tokens = [user.github_access_token for user in GfiUsers.objects()]
    if tokens:
        valid_tokens = list(set(tokens) - check_tokens(tokens))
        for query in GfiQueries.objects():
            if query.update_config:
                update_config = query.update_config
                task_id = update_config.task_id
                interval = update_config.interval
                scheduler.add_job(
                    update_gfi_info,
                    "interval",
                    args=[random.choice(valid_tokens), query.owner, query.name],
                    seconds=interval,
                    next_run_time=datetime.utcnow(),
                    id=task_id,
                )
                """update query begin time"""
                update_config.begin_time = datetime.utcnow()
                query.update(
                    update_config=update_config,
                )
                logger.info("Scheduled task: " + task_id + " added.")
    scheduler.start()
    logger.info("Scheduler started.")
    return scheduler


def daemon(init=False):
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
        if TOKENS:
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
    daemon(init=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true", default=False)
    should_init = parser.parse_args().init
    if should_init:
        initialize()
