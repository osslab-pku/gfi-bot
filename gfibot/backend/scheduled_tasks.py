"""
All functions below are scheduled tasks
Do NOT call them directly from the backend
"""

import argparse
import json
from pydoc import describe
from typing import Optional, Callable
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import wraps
import logging
import random
import datetime

import requests
import yagmail
from graphql import is_type_node
import mongoengine
from apscheduler.schedulers.background import BackgroundScheduler
from github import BadCredentialsException, RateLimitExceededException

from gfibot import CONFIG, TOKENS
from gfibot.data.update import update_repo
from gfibot.collections import *
from gfibot.check_tokens import check_tokens
from gfibot.data.dataset import get_dataset_for_repo, get_dataset_all

# from gfibot.model._predictor import (
#     update_training_summary,
#     update_prediction,
#     update_repo_prediction,
# )
from gfibot.model.predict import predict_repo

executor = ThreadPoolExecutor(max_workers=10)

logger = logging.getLogger(__name__)

DEFAULT_JOB_ID = "gfi_daemon"


def _add_comment_to_github_issue(
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


def _add_gfi_label_to_github_issue(
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


def _send_email(user_github_login: str, subject: str, body: str) -> bool:
    """
    Send email to user via yagmail
    """
    logger.info("send email to user {}".format(user_github_login))
    user_email = GfiUsers.objects(github_login=user_github_login).first().github_email
    if not user_email:
        logger.warning("User {} has no email".format(user_github_login))
        return False

    for e_obj in GfiEmail.objects():
        email = e_obj.email
        password = e_obj.password
        logger.info("Sending email to {} using {}".format(user_email, email))

        try:
            yag = yagmail.SMTP(email, password)
            yag.send(user_email, subject, body)
            return True
        except Exception as e:
            logger.warning("Error sending email: {}".format(e))

    return False


def _tag_and_comment(github_login, owner, name):
    """
    Add labels and comments (if necessary) to GitHub issue
    """
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
                    _add_gfi_label_to_github_issue(
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
                    _add_comment_to_github_issue(
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


def get_valid_tokens() -> List[str]:
    """
    Get valid tokens
    """
    tokens = [
        user.github_access_token
        for user in GfiUsers.objects()
        if user.github_access_token is not None
    ] + TOKENS
    return list(set(tokens) - check_tokens(tokens))


def update_gfi_info(token: str, owner: str, name: str, send_email: bool = False):
    """
    Repository manual updater (will block until done)
    token: GitHub token
    owner: GitHub repository owner
    name: GitHub repository name
    send_email: if True, send email to user
    """
    logger.info(
        "Updating gfi info for " + owner + "/" + name + " at {}.".format(datetime.now())
    )

    # 0. set state
    q = GfiQueries.objects(Q(name=name) & Q(owner=owner)).first()
    if q:
        if q.is_updating:
            logger.info("{}/{} is already updating.".format(owner, name))
            return
        q.update(is_updating=True, is_finished=False)

    try:
        # 1. fetch repo data
        try:
            update_repo(token, owner, name)
        except (BadCredentialsException, RateLimitExceededException) as e:
            # second try with a new token
            logger.error(e)
            valid_tokens = get_valid_tokens()
            if not valid_tokens:
                logger.error("No valid tokens found.")
                return
            random.seed(datetime.now())
            token = random.choice(valid_tokens)
            update_repo(token, owner, name)

        # 2. rebuild repo dataset
        begin_datetime = datetime(2008, 1, 1)
        get_dataset_for_repo(owner=owner, name=name, since=begin_datetime)

        # 3. update training summary
        # 4. update gfi prediction
        for newcomer_thres in [1, 2, 3, 4, 5]:
            predict_repo(owner=owner, name=name, newcomer_thres=newcomer_thres)

        # 5. tag, comment and email (if needed)
        user_github_login = None
        query = GfiQueries.objects(Q(name=name) & Q(owner=owner)).first()
        if query.is_github_app_repo and query.app_user_github_login:
            user_github_login = query.app_user_github_login
        if user_github_login:
            # submit and wait for the job to finish
            _tag_job = executor.submit(_tag_and_comment, user_github_login, owner, name)
            _tag_job.result()
        if user_github_login and send_email:
            _email_job = executor.submit(
                _send_email,
                user_github_login,
                "GFI-Bot: Update done for {}/{}".format(owner, name),
                "GFI-Bot: Update done for {}/{}".format(owner, name),
            )
            _email_job.result()
        logger.info(
            "Update done for " + owner + "/" + name + " at {}.".format(datetime.now())
        )

    # 6. set state
    finally:
        if q:
            q.update(is_updating=False, is_finished=True, is_pending=False)


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(daemon, "cron", hour=0, minute=0, id=DEFAULT_JOB_ID)
    valid_tokens = get_valid_tokens()
    if not valid_tokens:
        raise Exception("No valid tokens found.")
    for i, query in enumerate(GfiQueries.objects()):
        if query.update_config:
            update_config = query.update_config
            task_id = update_config.task_id
            interval = update_config.interval
            scheduler.add_job(
                update_gfi_info,
                "interval",
                args=[valid_tokens[i % len(valid_tokens)], query.owner, query.name],
                seconds=interval,
                next_run_time=datetime.utcnow(),
                id=task_id,
                replace_existing=True,
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

    valid_tokens = get_valid_tokens()
    if not valid_tokens:
        raise Exception("No valid tokens found.")
    if init:
        logger.info("Fetching ALL repo data from github")
        for i, project in enumerate(CONFIG["gfibot"]["projects"]):
            owner, name = project.split("/")
            update_repo(valid_tokens[i % len(valid_tokens)], owner, name)
    else:
        for i, repo in enumerate(list(Repo.objects().only("owner", "name"))):
            repo_query = GfiQueries.objects(
                Q(name=repo.name) & Q(owner=repo.owner)
            ).first()
            if not repo_query or not repo_query.update_config:
                logger.info(
                    "Fetching repo data from github: %s/%s", repo.owner, repo.name
                )
                update_repo(valid_tokens[i % len(valid_tokens)], repo.owner, repo.name)

    logger.info("Building dataset")
    get_dataset_all(datetime(2008, 1, 1))

    for threshold in [1, 2, 3, 4, 5]:
        for i, repo in enumerate(list(Repo.objects().only("owner", "name"))):
            repo_query = GfiQueries.objects(
                Q(name=repo.name) & Q(owner=repo.owner)
            ).first()
            if not repo_query or not repo_query.update_config:
                logger.info(
                    "Updating training summary and prediction: %s/%s@%d",
                    repo.owner,
                    repo.name,
                    threshold,
                )
                predict_repo(repo.owner, repo.name, newcomer_thres=threshold)

    logger.info("Daemon finished at " + str(datetime.now()))


def mongoengine_fork_safe_wrapper(*mongoengine_args, **mongoengine_kwargs):
    """
    Wrap a mongoengine function to make it fork safe
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            mongoengine.disconnect_all()
            mongoengine.connect(*mongoengine_args, **mongoengine_kwargs)
            try:
                return func(*args, **kwargs)
            finally:
                mongoengine.disconnect()

        return wrapper

    return decorator


@mongoengine_fork_safe_wrapper(
    db=CONFIG["mongodb"]["db"],
    host=CONFIG["mongodb"]["url"],
    tz_aware=True,
    uuidRepresentation="standard",
)
def update_repo_mp(token: str, owner: str, name: str):
    update_repo(token, owner, name)


@mongoengine_fork_safe_wrapper(
    db=CONFIG["mongodb"]["db"],
    host=CONFIG["mongodb"]["url"],
    tz_aware=True,
    uuidRepresentation="standard",
)
def update_training_summary_and_prediction_mp(owner: str, name: str, threshold: int):
    predict_repo(owner, name, newcomer_thres=threshold)


# @mongoengine_fork_safe_wrapper(
#     db=CONFIG["mongodb"]["db"],
#     host=CONFIG["mongodb"]["url"],
#     tz_aware=True,
#     uuidRepresentation="standard",
# )
# def update_prediction_mp(threshold: int):
#     update_prediction(threshold)


def daemon_mp(init=False, n_workers: Optional[int] = None):
    """
    Daemon updates repos without specific update config.
    init: if True, it will update all repos.
    n_workers: if not None, it will use n_workers to update repos.
        note that workers eat up loads of memory (~10GB each during model training)
    """
    logger.info("Daemon started at %s, workers=%s", str(datetime.now()), str(n_workers))

    mongoengine.connect(
        CONFIG["mongodb"]["db"],
        host=CONFIG["mongodb"]["url"],
        tz_aware=True,
        uuidRepresentation="standard",
        connect=False,
    )

    valid_tokens = get_valid_tokens()

    # 1. fetch data from github
    repos_to_update = []
    if init:
        repos_to_update = [
            (s.split("/")[0], s.split("/")[1]) for s in CONFIG["gfibot"]["projects"]
        ]
    else:
        for repo in Repo.objects():
            repo_query = GfiQueries.objects(
                Q(name=repo.name) & Q(owner=repo.owner)
            ).first()
            if (not repo_query) or (repo_query and not repo_query.update_config):
                repos_to_update.append((repo.owner, repo.name))
    logger.info("Fetching %d repos from github", len(repos_to_update))

    if n_workers is not None:
        with ProcessPoolExecutor(max_workers=n_workers):
            for i, (owner, name) in enumerate(repos_to_update):
                executor.submit(
                    update_repo_mp, valid_tokens[i % len(valid_tokens)], owner, name
                )
    else:
        for i, (owner, name) in enumerate(repos_to_update):
            update_repo(valid_tokens[i % len(valid_tokens)], owner, name)

    # 2. build dataset
    logger.info("Building dataset")
    get_dataset_all(datetime(2008, 1, 1), n_process=n_workers)

    # 3. update training summary
    # 4. update prediction
    if n_workers is not None:
        with ProcessPoolExecutor(max_workers=n_workers):
            for threshold in [1, 2, 3, 4, 5]:
                for i, (owner, name) in enumerate(repos_to_update):
                    executor.submit(
                        update_training_summary_and_prediction_mp,
                        owner,
                        name,
                        threshold,
                    )
    else:
        for threshold in [1, 2, 3, 4, 5]:
            for i, (owner, name) in enumerate(repos_to_update):
                predict_repo(owner, name, newcomer_thres=threshold)
            logger.info("Prediction updated for threshold %d", threshold)

    logger.info("Daemon finished at " + str(datetime.now()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser("GFI-Bot Dataset Builder")
    parser.add_argument(
        "--init", action="store_true", default=False, help="init dataset"
    )
    parser.add_argument(
        "--n_workers", type=int, default=None, help="number of workers to use"
    )
    args = parser.parse_args()

    # daemon_mp(args.init, args.n_workers)
    mongoengine.connect(
        CONFIG["mongodb"]["db"],
        host=CONFIG["mongodb"]["url"],
        tz_aware=True,
        uuidRepresentation="standard",
        connect=False,
    )
    daemon(args.init)
