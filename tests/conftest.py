import pytest
import logging
import mongoengine
import mongoengine.context_managers
from gfibot.backend.routes.user import github_login
import gfibot.model._predictor
import gfibot.model.base

from datetime import datetime, timezone
from gfibot import CONFIG, TOKENS
from gfibot.check_tokens import check_tokens
from gfibot.collections import *
from gfibot.data.dataset import *


@pytest.fixture(scope="session", autouse=True)
def execute_before_any_test():
    check_tokens(TOKENS)

    # Ensure that the production database is not touched in all tests
    CONFIG["mongodb"]["db"] = "gfibot-test"
    mongoengine.disconnect_all()

    gfibot.model._predictor.MODEL_ROOT_DIRECTORY = "models-test"
    gfibot.model.base.GFIBOT_MODEL_PATH = "models-test"
    os.makedirs("models-test", exist_ok=True)

    # don't start scheduler in tests
    os.environ["GFIBOT_SKIP_SCHEDULER"] = "1"
    # limit since_date in tests
    os.environ["CI"] = "1"


@pytest.fixture(scope="function")
def real_mongodb():
    """
    Prepare a real MongoDB instance for test usage.
    This fixture should only be used for test_all().
    """
    CONFIG["mongodb"]["db"] = "gfibot-test"

    conn = mongoengine.connect(
        CONFIG["mongodb"]["db"],
        host=CONFIG["mongodb"]["url"],
        tz_aware=True,
        uuidRepresentation="standard",
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
        CONFIG["mongodb"]["db"],
        host="mongomock://localhost",
        tz_aware=True,
        uuidRepresentation="standard",
    )
    # It seems that drop database does not work with mongomock
    collections = [
        Repo,
        RepoIssue,
        RepoCommit,
        RepoStar,
        OpenIssue,
        ResolvedIssue,
        Dataset,
        User,
        GfiUsers,
        GithubTokens,
        GfiQueries,
        GfiEmail,
        TrainingSummary,
        Prediction,
    ]
    for cls in collections:
        cls.drop_collection()

    repos = [
        Repo(
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            owner="owner",
            name="name",
            language="Python",
            topics=["topic1", "topic2"],
            description="Your Awesome Random APP",
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
                    month=datetime(2022, 1, 1, tzinfo=timezone.utc), count=3
                )
            ],
            monthly_pulls=[
                Repo.MonthCount(
                    month=datetime(2022, 1, 1, tzinfo=timezone.utc), count=1
                )
            ],
        ),
        Repo(
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            owner="owner2",
            name="name2",
            language="Python",
            topics=["topic1", "topic2"],
            description="Another Awesome Random Project",
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
                    month=datetime(2022, 1, 1, tzinfo=timezone.utc), count=3
                )
            ],
            monthly_pulls=[
                Repo.MonthCount(
                    month=datetime(2022, 1, 1, tzinfo=timezone.utc), count=1
                )
            ],
        ),
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
            labels=["bug"],
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
        RepoIssue(
            owner="owner",
            name="name",
            number=4,
            user="a2",
            state="open",
            created_at=datetime(2022, 1, 5, tzinfo=timezone.utc),
            closed_at=None,
            title="issue 4",
            body="issue 4 body",
            labels=["good first issue"],
            is_pull=False,
            merged_at=None,
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
    open_issues = [
        OpenIssue(
            owner="owner",
            name="name",
            number=4,
            created_at=datetime(2022, 1, 5, tzinfo=timezone.utc),
            updated_at=datetime(2022, 1, 5, tzinfo=timezone.utc),
            events=[
                IssueEvent(
                    type="labeled",
                    label="good first issue",
                    actor="a1",
                    time=datetime(2022, 1, 5, tzinfo=timezone.utc),
                )
            ],
        )
    ]
    users = [
        User(
            _created_at=datetime.utcnow(),
            _updated_at=datetime.utcnow(),
            name="a1",
            login="a1",
            issues=[
                User.Issue(
                    owner="owner",
                    name="name",
                    repo_stars=1,
                    state="closed",
                    number=1,
                    created_at=datetime(2022, 1, 1, tzinfo=timezone.utc),
                )
            ],
            pulls=[],
            pull_reviews=[],
            commit_contributions=[],
        ),
        User(
            _created_at=datetime.utcnow(),
            _updated_at=datetime.utcnow(),
            name="a2",
            login="a2",
            issues=[],
            pulls=[],
            pull_reviews=[],
            commit_contributions=[],
        ),
    ]
    datasets = [
        Dataset(
            owner="owner",
            name="name",
            number=5,
            created_at=datetime(1970, 1, 2, tzinfo=timezone.utc),
            closed_at=datetime(1970, 1, 3, tzinfo=timezone.utc),
            before=datetime(1970, 1, 3, tzinfo=timezone.utc),
            resolver_commit_num=1,
            title="title",
            body="body",
            len_title=1,
            len_body=1,
            n_code_snips=0,
            n_urls=0,
            n_imgs=0,
            coleman_liau_index=0.1,
            flesch_reading_ease=0.1,
            flesch_kincaid_grade=0.1,
            automated_readability_index=0.1,
            labels=["good first issue"],
            label_category=Dataset.LabelCategory(gfi=1),
            reporter_feat=Dataset.UserFeature(
                name="a1",
                n_commits=3,
                n_issues=1,
                n_pulls=2,
                resolver_commits=[4, 5, 6],
            ),
            owner_feat=Dataset.UserFeature(
                name="a2",
                n_commits=5,
                n_issues=1,
                n_pulls=2,
                resolver_commits=[1, 2, 3],
            ),
            n_stars=0,
            n_pulls=1,
            n_commits=5,
            n_contributors=2,
            n_closed_issues=1,
            n_open_issues=1,
            r_open_issues=1,
            issue_close_time=1.0,
            comment_users=[
                Dataset.UserFeature(
                    name="a3",
                    n_commits=5,
                    n_issues=1,
                    n_pulls=2,
                    resolver_commits=[1, 2],
                ),
                Dataset.UserFeature(
                    name="a4",
                    n_commits=3,
                    n_issues=1,
                    n_pulls=1,
                    resolver_commits=[4, 5],
                ),
            ],
        ),
        Dataset(
            owner="owner",
            name="name",
            number=6,
            created_at=datetime(1971, 1, 2, tzinfo=timezone.utc),
            closed_at=datetime(1971, 1, 3, tzinfo=timezone.utc),
            before=datetime(1971, 1, 3, tzinfo=timezone.utc),
            resolver_commit_num=3,
            title="title",
            body="body",
            len_title=1,
            len_body=1,
            n_code_snips=0,
            n_urls=0,
            n_imgs=0,
            coleman_liau_index=0.1,
            flesch_reading_ease=0.1,
            flesch_kincaid_grade=0.1,
            automated_readability_index=0.1,
            labels=[],
            label_category=Dataset.LabelCategory(gfi=1),
            reporter_feat=Dataset.UserFeature(
                name="a1",
                n_commits=3,
                n_issues=1,
                n_pulls=2,
                resolver_commits=[4, 5, 6],
            ),
            owner_feat=Dataset.UserFeature(
                name="a2",
                n_commits=5,
                n_issues=1,
                n_pulls=2,
                resolver_commits=[1, 2, 3],
            ),
            n_stars=0,
            n_pulls=1,
            n_commits=5,
            n_contributors=2,
            n_closed_issues=1,
            n_open_issues=1,
            r_open_issues=1,
            issue_close_time=1.0,
            comment_users=[
                Dataset.UserFeature(
                    name="a3",
                    n_commits=5,
                    n_issues=1,
                    n_pulls=2,
                    resolver_commits=[1, 2],
                ),
                Dataset.UserFeature(
                    name="a4",
                    n_commits=3,
                    n_issues=1,
                    n_pulls=1,
                    resolver_commits=[4, 5],
                ),
            ],
        ),
    ]
    github_tokens: List[GithubTokens] = [
        GithubTokens(
            app_name="app_name",
            client_id="this_is_not_a_client_id",
            client_secret="this_is_not_a_client_secret",
        ),
    ]
    gfi_users: List[GfiUsers] = [
        GfiUsers(
            github_id=1,
            github_access_token="this_is_not_access_token",
            github_app_token="this_is_not_app_token",
            github_login="chuchu",
            github_name="chu^2",
            user_queries=[
                GfiUsers.UserQuery(
                    repo="name",
                    owner="owner",
                    created_at=datetime(1970, 1, 1, tzinfo=timezone.utc),
                    increment=1,
                ),
                GfiUsers.UserQuery(
                    repo="name2",
                    owner="owner2",
                    created_at=datetime(1970, 1, 1, tzinfo=timezone.utc),
                    increment=1,
                ),
            ],
        ),
        GfiUsers(
            github_id=2,
            github_access_token="this_is_not_access_token",
            github_login="nobody",
            github_name="nobody",
            user_searches=[
                GfiUsers.UserQuery(
                    repo="name",
                    owner="owner",
                    created_at=datetime(1970, 1, 1, tzinfo=timezone.utc),
                    increment=i,
                )
                for i in range(3)
            ],
        ),
    ]
    gfi_queries: List[GfiQueries] = [
        GfiQueries(
            name="name",
            owner="owner",
            is_pending=False,
            is_finished=True,
            is_updating=False,
            is_github_app_repo=True,
            app_user_github_login="",
            _created_at=datetime(1970, 1, 1, tzinfo=timezone.utc),
            _finished_at=datetime(1970, 1, 1, tzinfo=timezone.utc),
            update_config=GfiQueries.GfiUpdateConfig(
                task_id="task_id",
                interval=24 * 3600,
                begin_time=datetime(1970, 1, 1, tzinfo=timezone.utc),
            ),
            repo_config=GfiQueries.GfiRepoConfig(
                newcomer_threshold=CONFIG["gfibot"]["default_newcomer_threshold"],
                gfi_threshold=CONFIG["gfibot"]["default_gfi_threshold"],
                need_comment=True,
                issue_tag="good first issue",
            ),
        ),
    ]
    gfi_emails: List[GfiEmail] = [
        GfiEmail(
            email="not.a.email.address@email.com",
            password="not_a.password",
        )
    ]
    training_summaries: List[TrainingSummary] = [
        TrainingSummary(
            owner="owner",
            name="name",
            threshold=CONFIG["gfibot"]["default_newcomer_threshold"],
            issues_train=[["a1", "a2"], ["a3", "a4"]],
            issues_test=[["a1", "a2"], ["a3", "a4"]],
            n_resolved_issues=3,
            n_newcomer_resolved=2,
            last_updated=datetime(1970, 1, 1, tzinfo=timezone.utc),
            r_newcomer_resolved=0.4,
            n_stars=10,
            n_gfis=2,
            issue_close_time=114514,
        ),
        TrainingSummary(
            owner="owner2",
            name="name2",
            threshold=CONFIG["gfibot"]["default_newcomer_threshold"],
            issues_train=[["a1", "a2"], ["a3", "a4"]],
            issues_test=[["a1", "a2"], ["a3", "a4"]],
            n_resolved_issues=3,
            n_newcomer_resolved=0,
            last_updated=datetime(1970, 1, 1, tzinfo=timezone.utc),
            r_newcomer_resolved=0.0,
            n_stars=15,
            accuracy=0.5,
            auc=0.6,
            issue_close_time=114,
        ),
    ]
    predictions: List[Prediction] = [
        Prediction(
            owner="owner",
            name="name",
            number=1,
            threshold=CONFIG["gfibot"]["default_newcomer_threshold"],
            probability=0.9,
            last_updated=datetime(1970, 1, 1, tzinfo=timezone.utc),
        ),
        Prediction(
            owner="owner",
            name="name",
            number=2,
            threshold=CONFIG["gfibot"]["default_newcomer_threshold"],
            probability=0.3,
            last_updated=datetime(1970, 1, 1, tzinfo=timezone.utc),
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
        resolved_issue.save()
        get_dataset(resolved_issue, resolved_issue.resolved_at)
        get_dataset(resolved_issue, resolved_issue.created_at)
    for open_issue in open_issues:
        open_issue.save()
        get_dataset(open_issue, open_issue.updated_at)
    for user in users:
        user.save()
    for dataset in datasets:
        dataset.save()
    for github_token in github_tokens:
        github_token.save()
    for gfi_user in gfi_users:
        gfi_user.save()
    for gfi_query in gfi_queries:
        gfi_query.save()
    for gfi_email in gfi_emails:
        gfi_email.save()
    for training_summary in training_summaries:
        training_summary.save()
    for prediction in predictions:
        prediction.save()

    yield

    mongoengine.disconnect()
