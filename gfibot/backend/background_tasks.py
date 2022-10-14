"""
All functions in this section are called from the backend
"""

import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Optional

import requests
from fastapi import HTTPException

from gfibot.collections import *
from gfibot.backend.scheduled_tasks import (
    update_gfi_info,
    get_valid_tokens,
    update_gfi_tags_and_comments,
)

logger = logging.getLogger(__name__)


def has_write_access(
    owner: str, name: str, user: Optional[str] = None, token: Optional[str] = None
) -> bool:
    """
    Check if {user} has write access to {owner}/{name}
    """
    if not token and user:
        user_record = (
            GfiUsers.objects(github_login=user)
            .only("github_access_token", "github_app_token")
            .first()
        )
        if not user_record:
            return False
        if (
            user_record.github_app_token
        ):  # user must have write access to install github app
            logging.debug("User %s registered with github app", user)
            return True
        token = user_record.github_access_token
    if not token:
        logging.debug("No token provided")
        return False
    url = f"https://api.github.com/repos/{owner}/{name}"
    response = requests.get(url, headers={"Authorization": f"token {token}"})
    if response.status_code == 200:
        data = response.json()
        try:
            if (
                data["permissions"]["push"]
                or data["permissions"]["admin"]
                or data["permissions"]["maintain"]
            ):
                logging.debug(
                    "User %s has privileges to write to %s/%s: %s",
                    user,
                    owner,
                    name,
                    str(data["permissions"]),
                )
                return True
        except KeyError:
            logging.debug(
                "User %s has no privileges to write to %s/%s: %s",
                user,
                owner,
                name,
                str(data["permissions"]),
            )
            return False
    return False


def add_repo_to_gfibot(owner: str, name: str, user: str) -> None:
    """
    Add repo to GFI-Bot (returns immediately)
        -> temp_worker (run once)
        -> scheduled_worker (run every day from tomorrow)
    """
    logger.info("Adding repo %s/%s on backend request", owner, name)
    user_record: GfiUsers = GfiUsers.objects(github_login=user).first()
    if not user_record:
        raise HTTPException(status_code=400, detail="User not found")
    if not has_write_access(owner, name, user):
        raise HTTPException(
            status_code=403, detail="You do not have write access to this repo"
        )
    # add to user_queries
    if not user_record.user_queries.filter(owner=owner, repo=name).first():
        user_record.user_queries.append(
            GfiUsers.UserQuery(
                owner=owner,
                repo=name,
                created_at=datetime.now(timezone.utc),
                increment=len(user_record.user_queries),
            )
        )
        user_record.save()
    # add to repo_queries
    q: Optional[GfiQueries] = GfiQueries.objects(name=name, owner=owner).first()
    if not q:
        logger.info("Adding repo %s/%s to GFI-Bot", owner, name)
        q = GfiQueries(
            name=name,
            owner=owner,
            is_pending=True,
            is_updating=False,
            is_finished=False,
            is_github_app_repo=True,
            app_user_github_login=user_record.github_login,
            _created_at=datetime.utcnow(),
            repo_config=GfiQueries.GfiRepoConfig(),
        )
    else:
        logger.info(f"update new query {name}/{owner}")
        q.update(
            is_github_app_repo=True,
            app_user_github_login=user_record.github_login,
        )

    if not q.update_config:  # create initial config
        q.update_config = GfiQueries.GfiUpdateConfig(
            task_id=f"{owner}-{name}-update",
            interval=24 * 3600,
        )

    q.save()

    token = (
        user_record.github_access_token
        if user_record.github_access_token
        else user_record.github_app_token
    )
    schedule_repo_update_now(owner=owner, name=name, token=token)
    from .server import get_scheduler

    scheduler = get_scheduler()
    if not scheduler.get_job(f"{owner}-{name}-update"):  # job not scheduled, create job
        scheduler.add_job(
            update_gfi_info,
            "interval",
            seconds=q.update_config.interval,
            next_run_time=datetime.utcnow()
            + timedelta(seconds=q.update_config.interval),
            id=f"{owner}-{name}-update",
            args=[token, owner, name, False],
            replace_existing=True,
        )


def schedule_repo_update_now(
    owner: str, name: str, token: Optional[str] = None, send_email: bool = False
) -> None:
    """
    Run a temporary repo update job once
    owner: Repo owner
    name: Repo name
    token: if None, random choice a token from the token pool
    send_email: if True, send email to user after update
    """
    from .server import get_scheduler

    scheduler = get_scheduler()

    job_id = f"{owner}-{name}-manual-update"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    if not token:
        valid_tokens = get_valid_tokens()
        if not valid_tokens:
            raise HTTPException(status_code=500, detail="No valid tokens available")
        # random choice 1 of the valid tokens
        random.seed(datetime.now())
        token = random.choice(valid_tokens)

    # run once
    scheduler.add_job(update_gfi_info, id=job_id, args=[token, owner, name, send_email])


def schedule_tag_task_now(owner: str, name: str, send_email: bool = False):
    """
    Run a temporary tag and comment job once
    owner: Repo owner
    name: Repo name
    token: if None, random choice a token from the token pool
    send_email: if True, send email to user after update
    """
    from .server import get_scheduler

    scheduler = get_scheduler()

    job_id = f"{owner}-{name}-manual-tag"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    # run once
    scheduler.add_job(
        update_gfi_tags_and_comments, id=job_id, args=[owner, name, send_email]
    )


def remove_repo_from_gfibot(owner: str, name: str, user: str) -> None:
    """
    Remove repo from GFI-Bot
    """
    logger.info("Removing repo %s/%s on backend request", owner, name)
    GfiUsers.objects(github_login=user).update(
        __raw__={"$pull": {"user_queries": {"repo": name, "owner": owner}}}
    )
    q = GfiQueries.objects(Q(name=name) & Q(owner=owner)).first()
    if not q:
        raise HTTPException(status_code=400, detail="Repo not found")
    q.delete()
    # delete job
    from .server import get_scheduler

    scheduler = get_scheduler()
    job_id = f"{owner}-{name}-update"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    # delete TrainingSummary
    TrainingSummary.objects(owner=owner, name=name).delete()
    # delete Repo
    Repo.objects(owner=owner, name=name).delete()
