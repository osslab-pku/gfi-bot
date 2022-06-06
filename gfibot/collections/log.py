import psutil
import logging

from datetime import datetime
from mongoengine import *


class Log(Document):
    owner: str = StringField(required=True)
    name: str = StringField(required=True)
    pid: int = IntField(required=True)
    user_github_login: str = StringField(null=True)
    update_begin: datetime = DateTimeField(required=True)
    update_end: datetime = DateTimeField(null=True)

    meta = {
        "allow_inheritance": True,
        "indexes": [
            {"fields": ["owner", "name"]},
            {"fields": ["user_github_login"]},
            {"fields": ["update_end"]},
        ],
    }


class GitHubFetchLog(Log):
    """A log describing a dataset fetch procedure"""

    updated_stars: int = IntField(null=True)
    updated_commits: int = IntField(null=True)
    updated_issues: int = IntField(null=True)
    updated_open_issues: int = IntField(null=True)
    updated_resolved_issues: int = IntField(null=True)
    updated_users: int = IntField(null=True)

    rate: int = IntField(null=True)
    rate_repo_stat: int = IntField(null=True)
    rate_resolved_issue: int = IntField(null=True)
    rate_open_issue: int = IntField(null=True)
    rate_user: int = IntField(null=True)


class DatasetBuildLog(Log):
    """A log describing a dataset build procedure"""

    updated_open_issues: int = IntField(null=True)
    updated_resolved_issues: int = IntField(null=True)


def log_exists(owner, name, log_type):
    existing_log: Log = log_type.objects(owner=owner, name=name, update_end=None)
    if existing_log.count() > 0:
        existing_log: Log = existing_log.first()
        if psutil.pid_exists(existing_log.pid):
            return True
        else:
            logging.warning(
                "%s/%s is being updated but its process is not running anymore",
                owner,
                name,
            )
            existing_log.delete()
    return False
