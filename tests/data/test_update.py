from gfibot import TOKENS
from pprint import pprint
from datetime import datetime
from gfibot.data.update import *


def test_count_by_month():
    c = count_by_month(
        [datetime(2020, 1, 1), datetime(2020, 1, 2), datetime(2021, 3, 4)]
    )
    print(c)
    assert c[0]["count"] == 2 and c[1]["count"] == 1


def test_match_issue_numbers():
    assert match_issue_numbers("abc") == []
    assert match_issue_numbers("close #db") == []
    assert match_issue_numbers("close #1 closes #2 closed #3") == [1, 2, 3]
    assert match_issue_numbers("fix #3 fiXes #2 fixed #1") == [3, 2, 1]
    assert match_issue_numbers("Resolve #2 resolves #1 resolved #3") == [2, 1, 3]


def test_locate_resolve_issues():
    owner, name = "HabitRPG", "habitica"
    issues = [
        {
            "owner": owner,
            "name": name,
            "number": 1,
            "user": "a1",
            "state": "closed",
            "created_at": datetime(1970, 1, 1, tzinfo=timezone.utc),
            "closed_at": datetime(1970, 1, 2, tzinfo=timezone.utc),
            "title": "",
            "body": "",
            "labels": [],
            "is_pull": False,
            "merged_at": None,
        },
        {
            "owner": owner,
            "name": name,
            "number": 12698,
            "user": "a1",
            "state": "closed",
            "created_at": datetime(1970, 1, 3, tzinfo=timezone.utc),
            "closed_at": datetime(1970, 1, 4, tzinfo=timezone.utc),
            "title": "",
            "body": "",
            "labels": [],
            "is_pull": False,
            "merged_at": None,
        },
        {
            "owner": owner,
            "name": name,
            "number": 12732,
            "user": "a1",
            "state": "closed",
            "created_at": datetime(1970, 1, 3, tzinfo=timezone.utc),
            "closed_at": datetime(1970, 1, 4, tzinfo=timezone.utc),
            "title": "",
            "body": "Fixes #12698",
            "labels": [],
            "is_pull": True,
            "merged_at": datetime(1970, 1, 4, tzinfo=timezone.utc),
        },
    ]
    commits = [
        {
            "owner": owner,
            "name": name,
            "sha": "50d4fff434ac6b7c6a728bd796413f279867f859",
            "author": "a1",
            "authored_at": datetime(1970, 1, 2, tzinfo=timezone.utc),
            "committer": "a1",
            "committed_at": datetime(1970, 1, 2, tzinfo=timezone.utc),
            "message": "fixes #1",
        }
    ]
    with Database() as db:
        for i in issues:
            db.repos.issues.replace_one(
                {"owner": owner, "name": name, "number": i["number"]},
                i,
                upsert=True,
            )
        for c in commits:
            db.repos.commits.replace_one(
                {"owner": owner, "name": name, "sha": c["sha"]},
                c,
                upsert=True,
            )

    token = TOKENS[0] if len(TOKENS) > 0 else None
    fetcher = RepoFetcher(token, owner, name)
    resolved = locate_resolved_issues(
        fetcher, datetime(1970, 1, 1, tzinfo=timezone.utc)
    )
    pprint(resolved)
    resolved = {r["number"]: r for r in resolved}
    assert resolved[1]["resolver"] == "a1" and resolved[1]["resolver_commit_num"] == 0
    assert (
        resolved[12698]["resolver"] == "a1"
        and resolved[12698]["resolver_commit_num"] == 1
    )


def test_update():
    token = TOKENS[0] if len(TOKENS) > 0 else None
    update(token, "octocat", "Hello-World")
    update(token, "octocat", "Hello-World")  # Update twice to test incremental update
