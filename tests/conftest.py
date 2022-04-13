import pytest
import logging
import mongoengine
import mongoengine.context_managers

from datetime import datetime, timezone
from gfibot import CONFIG
from gfibot.check_tokens import check_tokens
from gfibot.collections import *
from gfibot.data.dataset import *


@pytest.fixture(scope="session", autouse=True)
def execute_before_any_test():
    logging.basicConfig(level=logging.DEBUG)

    check_tokens()

    # Ensure that the production database is not touched in all tests
    CONFIG["mongodb"]["db"] = "gfibot-test"
    mongoengine.disconnect_all()


@pytest.fixture(scope="function")
def real_mongodb():
    """
    Prepare a real MongoDB instance for test usage.
    This fixture should only be used for test_all().
    """
    CONFIG["mongodb"]["db"] = "gfibot-test"

    conn = mongoengine.connect(
        CONFIG["mongodb"]["db"], host=CONFIG["mongodb"]["url"], tz_aware=True
    )
    conn.drop_database(CONFIG["mongodb"]["db"])

    yield

    mongoengine.disconnect()


@pytest.fixture(scope="function")
def mock_mongodb():
    """
    Prepare a mock MongoDB instance for test usage.
    This fixture can be used by any test that want some interaction with MongoDB.
    The MongoDB will contain some mock data for writing unit tests.
    """

    CONFIG["mongodb"]["db"] = "gfibot-test2"

    mongoengine.connect(
        CONFIG["mongodb"]["db"], host="mongomock://localhost", tz_aware=True
    )
    # It seems that drop database does not work with mongomock
    for cls in [Repo, RepoIssue, RepoCommit, RepoStar, ResolvedIssue, Dataset]:
        cls.drop_collection()

    repos = [
        Repo(
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            owner="owner",
            name="name",
            language="Python",
            repo_created_at=datetime(2022, 1, 1, tzinfo=timezone.utc),
            monthly_stars=[
                Repo.MonthCount(
                    month=datetime(2022, 1, 1, tzinfo=timezone.utc), count=1
                )
            ],
            monthly_commits=[
                Repo.MonthCount(
                    month=datetime(2022, 1, 1, tzinfo=timezone.utc), count=1
                )
            ],
            monthly_issues=[
                Repo.MonthCount(
                    month=datetime(2022, 1, 1, tzinfo=timezone.utc), count=2
                )
            ],
            monthly_pulls=[
                Repo.MonthCount(
                    month=datetime(2022, 1, 1, tzinfo=timezone.utc), count=1
                )
            ],
        )
    ]
    repo_commits = [
        RepoCommit(
            owner="owner",
            name="name",
            sha="50d4fff434ac6b7c6a728bd796413f279867f859",
            author="a1",
            authored_at=datetime(2022, 1, 2, tzinfo=timezone.utc),
            committer="a1",
            committed_at=datetime(2022, 1, 2, tzinfo=timezone.utc),
            message="fixes #1",
        )
    ]
    repo_issues = [
        RepoIssue(
            owner="owner",
            name="name",
            number=1,
            user="a1",
            state="closed",
            created_at=datetime(2022, 1, 1, tzinfo=timezone.utc),
            closed_at=datetime(2022, 1, 2, tzinfo=timezone.utc),
            title="issue 1",
            body="issue 1",
            labels=[],
            is_pull=False,
            merged_at=None,
        ),
        RepoIssue(
            owner="owner",
            name="name",
            number=2,
            user="a1",
            state="closed",
            created_at=datetime(2022, 1, 3, tzinfo=timezone.utc),
            closed_at=datetime(2022, 1, 4, tzinfo=timezone.utc),
            title="issue 2",
            body="issue 2",
            labels=[],
            is_pull=False,
            merged_at=None,
        ),
        RepoIssue(
            owner="owner",
            name="name",
            number=3,
            user="a1",
            state="closed",
            created_at=datetime(2022, 1, 3, tzinfo=timezone.utc),
            closed_at=datetime(2022, 1, 4, tzinfo=timezone.utc),
            title="PR 3",
            body="Fixes #2",
            labels=[],
            is_pull=True,
            merged_at=datetime(2022, 1, 4, tzinfo=timezone.utc),
        ),
    ]
    repo_stars = [
        RepoStar(
            owner="owner",
            name="name",
            user="a1",
            starred_at=datetime(2022, 1, 1, tzinfo=timezone.utc),
        )
    ]
    resolved_issues = [
        ResolvedIssue(
            owner="owner",
            name="name",
            number=1,
            created_at=datetime(2022, 1, 1, tzinfo=timezone.utc),
            resolved_at=datetime(2022, 1, 2, tzinfo=timezone.utc),
            resolver="a1",
            resolved_in="50d4fff434ac6b7c6a728bd796413f279867f859",
            resolver_commit_num=0,
            events=[],
        ),
        ResolvedIssue(
            owner="owner",
            name="name",
            number=2,
            created_at=datetime(2022, 1, 3, tzinfo=timezone.utc),
            resolved_at=datetime(2022, 1, 4, tzinfo=timezone.utc),
            resolver="a1",
            resolved_in=3,
            resolver_commit_num=1,
            events=[
                IssueEvent(
                    type="labeled",
                    label="bug",
                    actor="a1",
                    time=datetime(2022, 1, 3, tzinfo=timezone.utc),
                ),
                IssueEvent(
                    type="labeled",
                    label="gfi",
                    actor="a2",
                    time=datetime(2022, 1, 3, tzinfo=timezone.utc),
                ),
                IssueEvent(
                    type="unlabeled",
                    label="gfi",
                    actor="a2",
                    time=datetime(2022, 1, 3, tzinfo=timezone.utc),
                ),
                IssueEvent(
                    type="commented",
                    actor="a2",
                    time=datetime(2022, 1, 3, tzinfo=timezone.utc),
                    comment="a comment",
                ),
            ],
        ),
    ]

    for repo in repos:
        repo.save()
    for commit in repo_commits:
        commit.save()
    for issue in repo_issues:
        issue.save()
    for star in repo_stars:
        star.save()
    for resolved_issue in resolved_issues:
        ResolvedIssue.save(resolved_issue)
        get_dataset(resolved_issue, resolved_issue.resolved_at)
        get_dataset(resolved_issue, resolved_issue.created_at)

    yield

    mongoengine.disconnect()
