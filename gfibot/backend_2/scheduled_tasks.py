### Run scheduled tasks on APScheduler ###

import argparse
import mongoengine
from apscheduler.schedulers.background import BackgroundScheduler
from concurrent.futures import ThreadPoolExecutor
import logging
import random
import datetime
import requests
import json
import yagmail

from gfibot import CONFIG, TOKENS
from gfibot.data.update import update_repo
from gfibot.collections import *
from gfibot.check_tokens import check_tokens
from gfibot.data.dataset import get_dataset_for_repo, get_dataset_all
from gfibot.model.predictor import (
    update_training_summary,
    update_prediction,
    update_repo_prediction,
)

executor = ThreadPoolExecutor(max_workers=10)

logger = logging.getLogger(__name__)

DEFAULT_JOB_ID = "gfi_daemon"


def add_comment_to_github_issue(
    github_login, repo_name, repo_owner, issue_number, comment
):
    """
    Add comment to GitHub issue
    """
    user_token = GfiUsers.objects(Q(github_login=github_login)).first().github_app_token
    if user_token:
        headers = {
            "Authorization": "token {}".format(user_token),
            "Content-Type": "application/json",
        }
        url = "https://api.github.com/repos/{}/{}/issues/{}/comments".format(
            repo_owner, repo_name, issue_number
        )
        r = requests.post(url, headers=headers, data=json.dumps({"body": comment}))
        return r.status_code
    else:
        return 403


def add_comment_to_github_issue(
    github_login, repo_name, repo_owner, issue_number, comment
):
    """
    Add comment to GitHub issue
    """
    user_token = GfiUsers.objects(Q(github_login=github_login)).first().github_app_token
    if user_token:
        headers = {
            "Authorization": "token {}".format(user_token),
            "Content-Type": "application/json",
        }
        url = "https://api.github.com/repos/{}/{}/issues/{}/comments".format(
            repo_owner, repo_name, issue_number
        )
        r = requests.post(url, headers=headers, data=json.dumps({"body": comment}))
        return r.status_code
    else:
        return 403


def add_gfi_label_to_github_issue(
    github_login, repo_name, repo_owner, issue_number, label_name="good first issue"
):
    """
    Add label to Github issue
    """
    user_token = GfiUsers.objects(Q(github_login=github_login)).first().github_app_token
    if user_token:
        headers = {"Authorization": "token {}".format(user_token)}
        url = "https://api.github.com/repos/{}/{}/issues/{}/labels".format(
            repo_owner, repo_name, issue_number
        )
        r = requests.post(url, headers=headers, json=["{}".format(label_name)])
        return r.status_code
    else:
        return 403


def send_email(user_github_login, subject, body):
    """
    Send email to user
    """

    logger.info("send email to user {}".format(user_github_login))

    user_email = GfiUsers.objects(github_login=user_github_login).first().github_email

    email = GfiEmail.objects().first().email
    password = GfiEmail.objects().first().password

    logger.info("Sending email to {} using {}".format(user_email, email))

    if user_email != None:
        yag = yagmail.SMTP(email, password)
        yag.send(user_email, subject, body)
        yag.close()


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
    # update_training_summary(owner=owner, name=name)   # TODO: update training summary for a repo
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


def update_gfi_update_job(scheduler: BackgroundScheduler, job_id: str, name: str, owner: str):
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


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(daemon, "cron", hour=0, minute=0, id=DEFAULT_JOB_ID)
    tokens = [
        user.github_access_token
        for user in GfiUsers.objects()
        if user.github_access_token is not None
    ]
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
    """
    Daemon updates repos without specific update config.
    init: if True, it will update all repos.
    """
    logger.info("Daemon started at " + str(datetime.now()))

    tokens = [
        user.github_access_token
        for user in GfiUsers.objects()
        if user.github_access_token is not None
    ] + TOKENS
    if not tokens:
        logger.info("No tokens available.")
        return

    valid_tokens = list(set(tokens) - check_tokens(tokens))
    if init:
        logger.info("Fetching ALL repo data from github")
        for i, project in enumerate(CONFIG["gfibot"]["projects"]):
            owner, name = project.split("/")
            update_repo(valid_tokens[i % len(valid_tokens)], owner, name)
    else:
        for i, repo in enumerate(Repo.objects()):
            repo_query = GfiQueries.objects(Q(name=repo.name) & Q(owner=repo.owner)).first()
            if repo_query and not repo_query.update_config:
                logger.info("Fetching repo data from github: %s/%s", repo.owner, repo.name)
                update_repo(valid_tokens[i % len(valid_tokens)], repo.owner, repo.name)

    logger.info("Building dataset")
    get_dataset_all(datetime(2008, 1, 1))

    for threshold in [1, 2, 3, 4, 5]:
        update_training_summary(threshold)
        logger.info("Training summary updated for threshold %d", threshold)
        update_prediction(threshold)
        logger.info("Prediction updated for threshold %d", threshold)

    logger.info("Daemon finished at " + str(datetime.now()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser("GFI-Bot Dataset Builder")
    parser.add_argument("--init", action="store_true", default=False)
    mongoengine.connect(
        CONFIG["mongodb"]["db"],
        host=CONFIG["mongodb"]["url"],
        tz_aware=True,
        uuidRepresentation="standard",
        connect=False,
    )
    daemon(parser.parse_args().init)
