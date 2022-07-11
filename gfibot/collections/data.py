from typing import List, Union
from datetime import datetime
from mongoengine import *


class Dataset(Document):
    """
    The final dataset involved for RecGFI training
    All attributes are restored at a given time
    Attributes:
        owner, name, number: uniquely identifies a GitHub issue
        created_at: The time when the issue is created
        closed_at: The time when the issue is closed
        before: The time when all features in this document is computed
        resolver_commit_num: Issue resolver's commits to this repo, before the issue is resolved
                                if -1, means that the issue is still open
        ---------- Content ----------
        title: Issue title
        body: Issue description
        len_title: Length of issue title
        len_body: Length of issue description
        n_code_snips: The number of code snippets in issue body
        n_urls: The number of URLs in issue body
        n_imgs: The number of imgs in issue body
        coleman_liau_index: Readability index
        flesch_reading_ease: Readability index
        flesch_kincaid_grade: Readability index
        automated_readability_index: Readability index
        labels: The number of different labels
        ---------- Background ----------
        reporter_feat: Features for issue reporter
        owner_feat: Features for repository owner
        prev_resolver_commits: A list of the commits made by resolver for all previously resolved issues
        n_stars: Number of stars
        n_pulls: Number of pull requests
        n_commits: Number of commits
        n_contributors: Number of contributors
        n_closed_issues: Number of closed issues
        n_open_issues: Number of open issues
        r_open_issues: Ratio of open issues over all issues
        issue_close_time: Median issue close time (in seconds)
        ---------- Dynamics ----------
        comments: All issue comments
        events: All issue events, excluding comments
        comment_users: Features for all involved commenters
        event_users: Features for all involved users
    """

    class LabelCategory(EmbeddedDocument):
        """
        Each attribute represents the number of labels under this type.
        """

        bug: int = IntField(default=0)
        feature: int = IntField(default=0)
        test: int = IntField(default=0)
        build: int = IntField(default=0)
        doc: int = IntField(default=0)
        coding: int = IntField(default=0)
        enhance: int = IntField(default=0)

        gfi: int = IntField(default=0)
        medium: int = IntField(default=0)
        major: int = IntField(default=0)

        triaged: int = IntField(default=0)
        untriaged: int = IntField(default=0)

    class UserFeature(EmbeddedDocument):
        """User features in a dataset
        Attributes:
            name: GitHub username
            n_commits: Number of commits the user made to this repository
            n_issues: Number of issues the user opened in this repository
            n_pulls: Number of pull requests the user opened in this repository
            resolver_commits: For all resolved issue opened by this user,
                number of the resolver's commits prior to issue resolution
            n_repos: Number of repositories the user interacted with
            n_commits_all, n_issues_all, n_pulls_all, n_reviews_all:
                Number of commits, issues, pulls, and code reviews by this user
            max_stars_commit, max_stars_issue, max_stars_pull, max_stars_review
                For each of the four types of user interactions, maximum value of stars in their repo
                This may indicate the users' overall ability and/or reputation
        """

        name: str = StringField(required=True)
        n_commits: int = IntField(default=0, min_value=0)
        n_issues: int = IntField(default=0, min_value=0)
        n_pulls: int = IntField(default=0, min_value=0)
        resolver_commits: List[int] = ListField(IntField(min_value=0), default=[])
        n_repos: int = IntField(default=0, min_value=0)
        n_commits_all: int = IntField(default=0, min_value=0)
        n_issues_all: int = IntField(default=0, min_value=0)
        n_pulls_all: int = IntField(default=0, min_value=0)
        n_reviews_all: int = IntField(default=0, min_value=0)
        max_stars_commit: int = IntField(default=0, min_value=0)
        max_stars_issue: int = IntField(default=0, min_value=0)
        max_stars_pull: int = IntField(default=0, min_value=0)
        max_stars_review: int = IntField(default=0, min_value=0)

    owner: str = StringField(required=True)
    name: str = StringField(required=True)
    number: int = IntField(required=True)
    created_at: datetime = DateTimeField(required=True)
    closed_at: datetime = DateTimeField(null=True)
    before: datetime = DateTimeField(required=True)

    resolver_commit_num: int = IntField(required=True)

    # ---------- Content ----------

    title: str = StringField(required=True)
    body: str = StringField(required=True)
    len_title: int = IntField(required=True)
    len_body: int = IntField(required=True)
    n_code_snips: int = IntField(required=True)
    n_urls: int = IntField(required=True)
    n_imgs: int = IntField(required=True)
    coleman_liau_index: float = FloatField(required=True)
    flesch_reading_ease: float = FloatField(required=True)
    flesch_kincaid_grade: float = FloatField(required=True)
    automated_readability_index: float = FloatField(required=True)
    labels: List[str] = ListField(StringField(), default=[])
    label_category: LabelCategory = EmbeddedDocumentField(LabelCategory, required=True)

    # ---------- Background ----------

    reporter_feat: UserFeature = EmbeddedDocumentField(UserFeature, required=True)
    owner_feat: UserFeature = EmbeddedDocumentField(UserFeature, required=True)
    prev_resolver_commits: List[int] = ListField(IntField(), default=[])
    n_stars: int = IntField(required=True)
    n_pulls: int = IntField(required=True)
    n_commits: int = IntField(required=True)
    n_contributors: int = IntField(required=True)
    n_closed_issues: int = IntField(required=True)
    n_open_issues: int = IntField(required=True)
    r_open_issues: float = FloatField(required=True)
    issue_close_time: float = FloatField(required=True)

    # ---------- Dynamics ----------
    comments: List[str] = ListField(StringField(), default=[])
    events: List[str] = ListField(StringField(), default=[])
    comment_users: UserFeature = EmbeddedDocumentListField(UserFeature, default=[])
    event_users: UserFeature = EmbeddedDocumentListField(UserFeature, default=[])

    meta = {
        "indexes": [
            {"fields": ["owner", "name", "number", "before"], "unique": True},
        ]
    }


class IssueEvent(DynamicEmbeddedDocument):
    """
    Object representing issue events.
    For assigned, unassigned, labeled, unlabeled, referenced,
        cross-referenced, and commented events, additional fields are available.
    This document may contain **additional** fields depending on the specific event.
    Attributes:
        type: Type of the event
        time: The time when this event happened, can be null for some events
        actor: The GitHub user (login name) associated with the event, can be null for some events
    Attributes (for commented):
        comment: The comment text
        commenter: The commenter GitHub username
    Attributes (for labeled, unlabeled):
        label: The label name
    Attributes (for assigned, unassigned):
        assignee: The assignee name
    Attributes (for referenced, cross-referenced):
        source: The source of reference (an issue number), may be null
        commit: The commit SHA of the reference, may be null
    """

    type: str = StringField(required=True)
    time: datetime = DateTimeField(null=True)
    actor: str = StringField(null=True)
    comment: str = StringField(null=True)
    commenter: str = StringField(null=True)
    label: str = StringField(null=True)
    assignee: str = StringField(null=True)
    source: int = IntField(null=True)
    commit: str = StringField(null=True)


class ResolvedIssue(Document):
    """
    Additional issue information for issue that are resolved by a developer.
    These issues will be used as the training dataset for RecGFI training.
    """

    owner: str = StringField(required=True)
    name: str = StringField(required=True)
    number: int = IntField(required=True)

    created_at: datetime = DateTimeField(required=True)
    resolved_at: datetime = DateTimeField(required=True)
    resolver: str = StringField(required=True)  # Issue resolver's GitHub user name
    # If int, the PR number that resolved this issue.
    # If string, the commit hash that resolved this issue
    resolved_in: Union[int, str] = DynamicField(required=True)
    # Issue resolver's commits to this repo, before the issue is resolved
    resolver_commit_num: int = IntField(required=True)

    events: List[IssueEvent] = ListField(EmbeddedDocumentField(IssueEvent))

    meta = {"indexes": [{"fields": ["owner", "name", "number"], "unique": True}]}


class OpenIssue(Document):
    """
    Additional issue information for currently open issues.
    These issues will be used as the testing dataset for RecGFI training.
    """

    owner: str = StringField(required=True)
    name: str = StringField(required=True)
    number: int = IntField(required=True)
    created_at: datetime = DateTimeField(required=True)
    updated_at: datetime = DateTimeField(required=True)
    events: List[IssueEvent] = ListField(EmbeddedDocumentField(IssueEvent))
    meta = {"indexes": [{"fields": ["owner", "name", "number"], "unique": True}]}


class Repo(Document):
    """
    Repository statistics for both RecGFI training and web app.
    Attributes:
        created_at: The time when the repository was created in database
        updated_at: The time when the repository was last updated in database
        repo_created_at: The time when this repository is created in GitHub
        owner, name: Uniquely identifies a GitHub repository
        topics: A list of topics associated with the repository
        language: Main programming language (as returned by GitHub), can be None
        languages: All programming languages and their lines of code
        description: Repository description
        readme: Repostiory README content
        median_issue_close_time: The median time it takes to close an issue (in seconds)
        monthly_stars, monthly_commits, monthly_issues, monthly_pulls:
            Four time series describing number of new stars, commits, issues, and pulls
                in each month since repository creation
    """

    class LanguageCount(EmbeddedDocument):
        language: str = StringField(required=True)
        count: int = IntField(required=True)

    class MonthCount(EmbeddedDocument):
        month: datetime = DateTimeField(required=True)
        count: int = IntField(required=True, min_value=0)

    created_at: datetime = DateTimeField(required=True)
    updated_at: datetime = DateTimeField(required=True)
    repo_created_at: datetime = DateTimeField(required=True)
    owner: str = StringField(required=True)
    name: str = StringField(required=True)

    topics: List[str] = ListField(StringField(), default=[])
    language: str = StringField(null=True)
    languages: List[LanguageCount] = EmbeddedDocumentListField(
        LanguageCount, default=[]
    )
    description: str = StringField(null=True)
    readme: str = StringField(null=True)

    median_issue_close_time: float = FloatField(null=True)
    monthly_stars: List[MonthCount] = EmbeddedDocumentListField(MonthCount, default=[])
    monthly_commits: List[MonthCount] = EmbeddedDocumentListField(
        MonthCount, default=[]
    )
    monthly_issues: List[MonthCount] = EmbeddedDocumentListField(MonthCount, default=[])
    monthly_pulls: List[MonthCount] = EmbeddedDocumentListField(MonthCount, default=[])

    meta = {"indexes": [{"fields": ["owner", "name"], "unique": True}, "#language", 
        {"fields": ["$owner", "$name", "$description"], "language_override": "english", 
        "weights": {"owner": 2, "name": 2, "description": 1}}]}


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

    meta = {
        "indexes": [
            {"fields": ["owner", "name", "sha"], "unique": True},
            {"fields": ["author"]},
            {"fields": ["authored_at"]},
            {"fields": ["committer"]},
            {"fields": ["committed_at"]},
        ]
    }


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

    meta = {
        "indexes": [
            {"fields": ["owner", "name", "number"], "unique": True},
            {"fields": ["is_pull"]},
            {"fields": ["created_at"]},
        ],
    }


class RepoStar(Document):
    """Repository star statistics for RecGFI training"""

    owner: str = StringField(required=True)
    name: str = StringField(required=True)
    # GitHub username who starred this repository
    user: str = StringField(required=True)
    starred_at: datetime = DateTimeField(required=True)  # Time of the starred event

    meta = {"indexes": [{"fields": ["owner", "name", "user"], "unique": True}]}


class User(Document):
    """User statistics for RecGFI training"""

    class Issue(EmbeddedDocument):
        # repo info
        owner: str = StringField(required=True)
        name: str = StringField(required=True)
        repo_stars: int = IntField(required=True, min_value=0)
        # issue number (state can not be updated incrementally)
        state: str = StringField(required=True)
        number: int = IntField(required=True, min_value=0)
        created_at: datetime = DateTimeField(required=True)

    class Pull(EmbeddedDocument):
        # repo info
        owner: str = StringField(required=True)
        name: str = StringField(required=True)
        repo_stars: int = IntField(required=True, min_value=0)
        # pull request number  (state can not be updated incrementally)
        state: str = StringField(required=True)
        number: int = IntField(required=True)
        created_at: datetime = DateTimeField(required=True)

    class Review(EmbeddedDocument):
        # repo info
        owner: str = StringField(required=True)
        name: str = StringField(required=True)
        repo_stars: int = IntField(required=True, min_value=0)
        # review number & state
        number: int = IntField(required=True)
        state: str = StringField(required=True)
        created_at: datetime = DateTimeField(required=True)

    class CommitContribution(EmbeddedDocument):
        # repo info
        owner: str = StringField(required=True)
        name: str = StringField(required=True)
        repo_stars: int = IntField(required=True, min_value=0)
        # commit count
        commit_count: int = IntField(required=True, min_value=0)
        created_at: datetime = DateTimeField(required=True)

    _created_at: datetime = DateTimeField(required=True)  # created in the database
    _updated_at: datetime = DateTimeField(required=True)  # updated in the database

    name: str = StringField(null=True)
    login: str = StringField(required=True)
    # issues, issueComments, pulls (use end cursor to paginate)
    issues: List[Issue] = EmbeddedDocumentListField(Issue)
    pulls: List[Pull] = EmbeddedDocumentListField(Pull)
    # reviews, commits (use date to paginate)
    pull_reviews: List[Review] = EmbeddedDocumentListField(Review)
    commit_contributions: List[CommitContribution] = EmbeddedDocumentListField(
        CommitContribution
    )

    meta = {
        "indexes": [
            {"fields": ["login"], "unique": True},
            {"fields": ["issues.owner", "issues.name"]},
            {"fields": ["issues.created_at"]},
            {"fields": ["pulls.owner", "pulls.name"]},
            {"fields": ["pulls.created_at"]},
            {"fields": ["pull_reviews.owner", "pull_reviews.name"]},
            {"fields": ["pull_reviews.created_at"]},
            {"fields": ["commit_contributions.owner", "commit_contributions.name"]},
            {"fields": ["commit_contributions.created_at"]},
        ]
    }
