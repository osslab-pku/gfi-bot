from typing import List, Union
from datetime import datetime
from mongoengine import *


class Dataset(Document):
    """
    The final dataset involved for RecGFI training
    All attributes are restored at the time of issue resolution

    Attributes:
        owner: The user who owns the dataset
        name: The name of the dataset
        number: Issue number in GitHub
        clst: The time when the issue is closed

        resolver_commit_num: Issue resolver's commits to this repo, before the issue is resolved

        ---------- Content ----------

        title: Issue title
        body: Issue description
        length_of_title: Length of issue title
        length_of_description: Length of issue description
        num_of_code: The number of code snippets in issue body
        num_of_urls: The number of URLs in issue body
        num_of_pics: The number of pictures in issue body
        coleman_liau_index: Readability index
        flesch_reading_ease: Readability index
        flesch_kincaid_grade: Readability index
        automated_readability_index: Readability index
        labels: The number of different labels

        ---------- Background ----------

        isslist: List of resolver_commit_num for issues in repository
        pro_star: Issue's repository star
        propr: The number of repository PRs
        procmt: The number of commits in repo
        contributornum: The number of issues in repo
        crtclsissnum: The number of closed issues
        openiss: The number of open issues
        openissratio: The ratio of open/all issues
        clsisst: The median time for issues to be closed

        rptcmt: The number of commits in repo from the reporter
        rptiss: The number of issues in repo from the reporter
        rptpr: The number of PRs from the reporter
        rptissues: resolver_commit_num of issues reported by the owner

        ownercmt: The number of commits from the owner
        owneriss: The number of issues from the owner
        ownerpr: The number of PRs from the owner
        ownerissues: resolver_commit_num of issues reported by the owner

        ---------- Dynamics ----------

        commentnum: Number of comments
        comment: Issue comments
        commentusers: Experience of commenters
        events: Experience of eventers
        rpthasevent: If reporter attended events in the issue
        rpthascomment: If reporter commented in the issue
    """

    owner = StringField(required=True)
    name = StringField(required=True)
    number = StringField(required=True)
    clst = DateTimeField(required=True)

    resolver_commit_num = IntField(required=True)

    # ---------- Content ----------

    title = StringField(required=True)
    body = StringField(required=True)
    length_of_title = IntField(required=True)
    length_of_description = IntField(required=True)
    num_of_code = IntField(required=True)
    num_of_urls = IntField(required=True)
    num_of_pics = IntField(required=True)
    coleman_liau_index = FloatField(required=True)
    flesch_reading_ease = FloatField(required=True)
    flesch_kincaid_grade = FloatField(required=True)
    automated_readability_index = FloatField(required=True)
    labels = ListField(IntField(), required=True)

    # ---------- Background ----------

    isslist = ListField(IntField(), required=True)
    pro_star = IntField(required=True)
    propr = IntField(required=True)
    procmt = IntField(required=True)
    contributornum = IntField(required=True)
    crtclsissnum = IntField(required=True)
    openiss = IntField(required=True)
    openissratio = FloatField(required=True)
    clsisst = FloatField(required=True)

    rptcmt = IntField(required=True)
    rptiss = IntField(required=True)
    rptpr = IntField(required=True)
    rptissues = ListField(IntField(), required=True)

    ownercmt = IntField(required=True)
    owneriss = IntField(required=True)
    ownerpr = IntField(required=True)
    ownerissues = ListField(IntField(), required=True)

    # ---------- Dynamics ----------

    commentnum = IntField(required=True)
    comment = StringField(required=True)
    events = ListField(DynamicField(), required=True)
    commentusers = ListField(DynamicField(), required=True)
    rpthasevent = IntField(required=True)
    rpthascomment = IntField(required=True)

    meta = {
        "indexes": [
            {"fields": ["owner", "name", "number"], "unique": True},
            {"fields": ["clst"]},
        ]
    }


class ResolvedIssue(Document):
    """
    Additional issue information for issue that are resolved by a developer.
    These issues will be used as the training dataset for RecGFI training.
    """

    class Event(DynamicEmbeddedDocument):
        """
        Object representing issue events.
        For assigned, unassigned, labeled, unlabeled, referenced,
            cross-referenced, and commented events, additional fields are available.
        This document may contain additional fields depending on the specific event.

        Attributes:
            type: Type of the event
            time: The time when this event happened, can be null for some events
            actor: The GitHub user (login name) associated with the event, can be null for some events
        """

        type: str = StringField(required=True)
        time: datetime = DateTimeField(null=True)
        actor: str = StringField(null=True)

    owner: str = StringField(required=True)
    name: str = StringField(required=True)
    number: int = IntField(required=True)

    # Issue resolver's GitHub user name
    resolver: str = StringField(required=True)
    # If int, the PR number that resolved this issue.
    # If string, the commit hash that resolved this issue
    resolved_in: Union[int, str] = DynamicField(
        required=True, validation=lambda x: isinstance(x, (int, str))
    )
    # Issue resolver's commits to this repo, before the issue is resolved
    resolver_commit_num: int = IntField(required=True)

    events: List[Event] = ListField(EmbeddedDocumentField(Event))

    meta = {"indexes": [{"fields": ["owner", "name", "number"], "unique": True}]}


class Repo(Document):
    """Repository statistics for RecGFI training"""

    class MonthCount(EmbeddedDocument):
        month: datetime = DateTimeField(required=True)
        count: int = IntField(required=True, min_value=0)

    created_at: datetime = DateTimeField(required=True)
    updated_at: datetime = DateTimeField(required=True)
    owner: str = StringField(required=True)
    name: str = StringField(required=True)

    # Main programming language (as returned by GitHub), can be None
    language: str = StringField(null=True)

    # The time when this repository is created in GitHub
    repo_created_at: datetime = DateTimeField(required=True)

    # Four time series describing number of new stars, commits, issues, and pulls
    #     in each month since repository creation
    monthly_stars: MonthCount = EmbeddedDocumentListField(MonthCount)
    monthly_commits: MonthCount = EmbeddedDocumentListField(MonthCount)
    monthly_issues: MonthCount = EmbeddedDocumentListField(MonthCount)
    monthly_pulls: MonthCount = EmbeddedDocumentListField(MonthCount)

    meta = {"indexes": [{"fields": ["owner", "name"], "unique": True}]}


class RepoCommit(Document):
    """Repository commit statistics for RecGFI training"""

    owner: str = StringField(required=True)
    name: str = StringField(required=True)
    sha: str = StringField(required=True)

    # GitHub username of the commit author, can be None
    author: str = StringField(null=True)
    authored_at: datetime = DateTimeField(required=True)

    # GitHub username of the committer, can be None
    committer: str = StringField(null=True)
    committed_at: datetime = DateTimeField(required=True)

    message: str = StringField(required=True)

    meta = {"indexes": [{"fields": ["owner", "name", "sha"], "unique": True}]}


class RepoIssue(Document):
    """
    Repository issue statistics for RecGFI training.
    Note that pull requests are also included in this collection
    """

    owner: str = StringField(required=True)
    name: str = StringField(required=True)
    number: int = IntField(required=True, min_value=0)

    # GitHub username of the issue reporter / PR submitter
    user: str = StringField(required=True)
    state: str = StringField(required=True, choices=("open", "closed"))
    created_at: datetime = DateTimeField(
        required=True
    )  # The time when this issue/PR is created
    closed_at: datetime = DateTimeField(
        null=True
    )  # The time when this issue/PR is closed
    is_pull: bool = BooleanField(required=True)  # Whether the issue is a pull request
    merged_at: datetime = DateTimeField(
        null=True
    )  # If a PR, the time when this PR is merged

    title: str = StringField(required=True)
    body: str = StringField(null=True)
    labels: List[str] = ListField(StringField(required=True))

    meta = {"indexes": [{"fields": ["owner", "name", "number"], "unique": True}]}


class RepoStar(Document):
    """Repository star statistics for RecGFI training"""

    owner: str = StringField(required=True)
    name: str = StringField(required=True)
    user: str = StringField(
        required=True
    )  # GitHub username who starred this repository
    starred_at: datetime = DateTimeField(required=True)  # Time of the starred event

    meta = {"indexes": [{"fields": ["owner", "name", "user"], "unique": True}]}


class User(Document):
    """User statistics for RecGFI training (TODO: This documentation is not finalized yet)"""

    class Repo(EmbeddedDocument):
        name: str = StringField(required=True)
        created_at: datetime = DateTimeField(required=True)

    class Issue(EmbeddedDocument):
        owner: str = StringField(required=True)
        name: str = StringField(required=True)
        number: int = IntField(required=True)
        created_at: datetime = DateTimeField(required=True)

    class Pull(EmbeddedDocument):
        owner: str = StringField(required=True)
        name: str = StringField(required=True)
        number: int = IntField(required=True)
        created_at: datetime = DateTimeField(required=True)

    created_at: datetime = DateTimeField(required=True)
    updated_at: datetime = DateTimeField(required=True)
    username: str = StringField(required=True, unique=True)
    repos: Repo = EmbeddedDocumentListField(Repo)
    issues: Issue = EmbeddedDocumentListField(Issue)
    pulls: Pull = EmbeddedDocumentListField(Pull)
    meta = {"indexes": [{"fields": ["username"], "unique": True}]}
