import pymongo
import gfibot.data.rest as rest

from pprint import pprint
from datetime import datetime, timedelta, timezone
from gfibot import TOKENS, Database


def test_page_num():
    assert rest.get_page_num(30, 90) == 3
    assert rest.get_page_num(30, 91) == 4


def test_get_month_interval():
    since, until = rest.get_month_interval(datetime(2020, 1, 12, tzinfo=timezone.utc))
    print(since, until)
    assert (since - timedelta(seconds=1)).month == 12
    assert (until + timedelta(seconds=1)).month == 2


def test_repo_fetcher():
    now = datetime.now(timezone.utc)
    owner, name = "octocat", "hello-world"
    token = TOKENS[0] if len(TOKENS) > 0 else None
    fetcher = rest.RepoFetcher(token, owner, name)

    stats = fetcher.get_stats()
    pprint(stats)
    assert (
        stats["name"].lower() == name
        and stats["owner"].lower() == owner
        and stats["repo_created_at"] < now
    )

    assert fetcher.get_commits_in_month(now) == 0

    stars = fetcher.get_stars(since=now - timedelta(days=7))
    pprint(stars)
    for star in stars:
        with Database() as db:
            db.repo.stars.insert_one(star)

    commits = fetcher.get_commits(since=datetime(2000, 1, 1, tzinfo=timezone.utc))
    pprint(commits)
    assert len(commits) > 0
    for commit in commits:
        with Database() as db:
            db.repo.commits.insert_one(commit)

    issues = fetcher.get_issues(since=now - timedelta(days=3))
    pprint(issues)
    assert len(issues) >= 0
    for issue in issues:
        with Database() as db:
            db.repo.issues.insert_one(issue)
