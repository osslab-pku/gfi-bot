import requests
import yagmail
import logging
import json
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from gfibot.collections import *
from gfibot.data.update import update_repo
from gfibot.data.dataset import get_dataset_for_repo
from gfibot.model.predictor import update_repo_prediction, update_training_summary

logger = logging.getLogger(__name__)


def add_repo_worker(owner: str, name: str, token: str) -> None:
    """
    Add repo to dataset
    """
    logger.info("Adding repo {}/{} on backend request", owner, name)
    # create task
    GfiQueries(
        name=name,
        owner=owner,
        is_pending=True,
        is_finished=False,
        _created_at=datetime.utcnow(),
        is_github_app_repo=False,
        repo_config=GfiQueries.GfiRepoConfig(),
        update_config=GfiQueries.GfiUpdateConfig(
            task_id=f"{owner}-{name}-update",
        ),
    ).save()
    try:
        update_repo(token, owner, name)
        get_dataset_for_repo(owner, name, since=datetime(2008, 1, 1))
        update_repo_prediction(owner, name)
        # update_training_summary(3)  # threshold=3 rank repos
        # task is finished
        GfiQueries.objects(Q(owner=owner) & Q(name=name)).update_one(
            set__is_pending=False,
            set__is_finished=True,
            set__is_updating=False,
            set___finished_at=datetime.now(tz=timezone.utc),
        )
    except Exception as e:
        # delete task
        GfiQueries.objects(Q(owner=owner) & Q(name=name)).delete()
        logger.error("Exception in add_repo_worker: {}/{}".format(owner, name), e)





