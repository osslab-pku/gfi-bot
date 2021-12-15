import logging
import argparse

from typing import List, Dict, Any
from collections import Counter
from datetime import datetime, timezone

from .. import CONFIG, TOKENS, Database
from .rest import RepoFetcher, logger as rest_logger


logger = logging.getLogger(__name__)


def count_by_month(dates: List[datetime]) -> List[Dict[str, Any]]:
    counts = Counter(map(lambda d: (d.year, d.month), dates))
    return sorted(
        [
            {"month": datetime(year=y, month=m, day=1, tzinfo=timezone.utc), "count": c}
            for (y, m), c in counts.items()
        ],
        key=lambda k: k["month"],
    )


def update_repo(fetcher: RepoFetcher) -> Dict[str, Any]:
    logger.info("Updating repo: %s/%s", fetcher.owner, fetcher.name)
    with Database() as db:
        repo = db.repos.find_one({"owner": fetcher.owner, "name": fetcher.name})
    if repo is None:
        logger.info("Repo not found in database, creating...")
        repo = {
            "created_at": datetime.now(timezone.utc),
            "updated_at": None,
            "owner": fetcher.owner,
            "name": fetcher.name,
            "language": None,
            "repo_created_at": None,
            "monthly_stars": [],
            "monthly_commits": [],
            "monthly_issues": [],
        }

    for k, v in fetcher.get_stats().items():
        repo[k] = v
    logger.info("Repo stats updated, rate remaining %s", fetcher.gh.rate_limiting)
    return repo


def update_stars(fetcher: RepoFetcher, since: datetime) -> List[Dict[str, Any]]:
    stars = fetcher.get_stars(since)
    logger.info(
        "%d stars updated, rate remaining %s",
        len(stars),
        fetcher.gh.rate_limiting,
    )
    with Database() as db:
        for star in stars:
            db.repos.stars.replace_one(
                {"owner": fetcher.owner, "name": fetcher.name, "user": star["user"]},
                star,
                upsert=True,
            )
    return stars


def update_commits(fetcher: RepoFetcher, since: datetime) -> List[Dict[str, Any]]:
    commits = fetcher.get_commits(since)
    logger.info(
        "%d commits updated, rate remaining %s",
        len(commits),
        fetcher.gh.rate_limiting,
    )
    with Database() as db:
        for commit in commits:
            db.repos.commits.replace_one(
                {
                    "owner": fetcher.owner,
                    "name": fetcher.name,
                    "sha": commit["sha"],
                },
                commit,
                upsert=True,
            )
    return commits


def update_issues(fetcher: RepoFetcher, since: datetime) -> List[Dict[str, Any]]:
    issues = fetcher.get_issues(since)
    logger.info(
        "%d issues updated, rate remaining %s",
        len(issues),
        fetcher.gh.rate_limiting,
    )
    with Database() as db:
        for issue in issues:
            db.repos.issues.replace_one(
                {
                    "owner": fetcher.owner,
                    "name": fetcher.name,
                    "number": issue["number"],
                },
                issue,
                upsert=True,
            )
    return issues


def update(token: str, owner: str, name: str) -> None:
    fetcher = RepoFetcher(token, owner, name)
    repo = update_repo(fetcher)

    if repo["updated_at"] is None:
        since = repo["repo_created_at"]
    else:
        since = repo["updated_at"]
    repo["updated_at"] = datetime.now(timezone.utc)

    logging.info("Update stars, commits, and issues since %s", since)
    stars = update_stars(fetcher, since)
    commits = update_commits(fetcher, since)
    issues = update_issues(fetcher, since)

    repo["monthly_stars"] = count_by_month([s["starred_at"] for s in stars])
    repo["monthly_commits"] = count_by_month([c["committed_at"] for c in commits])
    repo["monthly_issues"] = count_by_month(
        [i["created_at"] for i in issues if not i["is_pull"]]
    )
    repo["monthly_pulls"] = count_by_month(
        [i["created_at"] for i in issues if i["is_pull"]]
    )

    with Database() as db:
        db.repos.replace_one(
            {"owner": fetcher.owner, "name": fetcher.name}, repo, upsert=True
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
        rest_logger.setLevel(logging.DEBUG)

    for i, project in enumerate(CONFIG["gfibot"]["projects"]):
        owner, name = project.split("/")
        update(TOKENS[i % len(TOKENS)], owner, name)

    logger.info("Done!")
