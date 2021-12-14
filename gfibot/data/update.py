import logging
import pymongo
import argparse

from typing import Dict, Any
from datetime import datetime, timezone
from dateutil import rrule

from .. import CONFIG, TOKENS, Database
from .rest import RepoFetcher, logger as rest_logger


logger = logging.getLogger(__name__)


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
            "stars": [],
            "commits": [],
        }

    for k, v in fetcher.get_stats().items():
        repo[k] = v
    logger.info("Repo stats updated, rate remaining %s", fetcher.gh.rate_limiting)

    months = list(
        rrule.rrule(
            rrule.MONTHLY,
            dtstart=repo["repo_created_at"],
            until=datetime.now(timezone.utc),
        )
    )

    existing_months = {(m["month"].year, m["month"].month) for m in repo["commits"]}
    for month in months:
        if (month.year, month.month) not in existing_months:
            logger.debug("Updating commits at %d-%d", month.year, month.month)
            repo["commits"].append(
                {
                    "month": month.replace(
                        day=1, hour=0, minute=0, second=0, microsecond=0
                    ),
                    "count": fetcher.get_commits_in_month(month),
                }
            )
    repo["commits"] = sorted(repo["commits"], key=lambda c: c["month"])
    logger.info(
        "%d months of commits (%d updated), rate remaining %s",
        len(repo["commits"]),
        len(months) - len(existing_months),
        fetcher.gh.rate_limiting,
    )

    return repo


def update_stars(fetcher: RepoFetcher, since: datetime) -> None:
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


def update_commits(fetcher: RepoFetcher, since: datetime) -> None:
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


def update_issues(fetcher: RepoFetcher, since: datetime) -> None:
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


def update(token: str, owner: str, name: str) -> None:
    fetcher = RepoFetcher(token, owner, name)
    repo = update_repo(fetcher)

    if repo["updated_at"] is None:
        since = repo["repo_created_at"]
    else:
        since = repo["updated_at"]
    repo["updated_at"] = datetime.now(timezone.utc)

    logging.info("Update stars, commits, and issues since %s", since)
    update_stars(fetcher, since)
    update_commits(fetcher, since)
    update_issues(fetcher, since)

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
