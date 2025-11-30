import psutil
import logging
from datetime import datetime
from mongoengine import Document, StringField, IntField, DateTimeField


class Log(Document):
    owner = StringField(required=True)
    name = StringField(required=True)
    pid = IntField(required=True)
    user_github_login = StringField()
    update_begin = DateTimeField(required=True)
    update_end = DateTimeField()

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
    updated_stars = IntField()
    updated_commits = IntField()
    updated_issues = IntField()
    updated_open_issues = IntField()
    updated_resolved_issues = IntField()
    updated_users = IntField()
    rate = IntField()
    rate_repo_stat = IntField()
    rate_resolved_issue = IntField()
    rate_open_issue = IntField()
    rate_user = IntField()


class DatasetBuildLog(Log):
    """A log describing a dataset build procedure"""
    updated_open_issues = IntField()
    updated_resolved_issues = IntField()


def update_in_progress(owner, name, log_type):
    """
    Efficiently checks if an update process is already running.
    Uses only one DB query and minimal data retrieval.
    """
    # Fetch only the fields we need
    existing_log = log_type.objects(owner=owner, name=name, update_end=None).only("pid").first()

    if not existing_log:
        return False

    if psutil.pid_exists(existing_log.pid):
        return True

    # Process not running — clean up stale log
    logging.warning(
        "Stale log found for %s/%s (PID %d not running) — deleting entry.",
        owner, name, existing_log.pid
    )
    existing_log.delete()
    return False
