from datetime import datetime
from mongoengine import *


class GitHubFetchLog(Document):
    """A log describing a dataset fetch procedure"""

    owner: str = StringField(required=True)
    name: str = StringField(required=True)
    user_github_login: str = StringField(null=True)
    update_begin: datetime = DateTimeField(required=True)
    update_end: datetime = DateTimeField(null=True)

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

    meta = {
        "collection": "github_fetch_log",
        "indexes": [
            {"fields": ["owner", "name"]},
            {"fields": ["user_github_login"]},
            {"fields": ["update_end"]},
        ],
    }


class DatasetBuildLog(Document):
    """A log describing a dataset build procedure"""

    owner: str = StringField(required=True)
    name: str = StringField(required=True)
    user_github_login: str = StringField(null=True)
    update_begin: datetime = DateTimeField(required=True)
    update_end: datetime = DateTimeField(required=True)
    updated_open_issues: int = IntField(required=True)
    updated_resolved_issues: int = IntField(required=True)
