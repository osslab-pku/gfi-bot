import logging
import pymongo

from typing import Dict, Any
from datetime import datetime, timezone
from dateutil import rrule
from .. import CONFIG, TOKENS
from .rest import RepoFetcher


logger = logging.getLogger(__name__)


def update_repo(fetcher: RepoFetcher) -> Dict[str, Any]:
    logger.info("Updating repo: %s/%s", owner, name)
    with pymongo.MongoClient(CONFIG["mongodb"]["url"]) as client:
        repo = client.gfibot.repos.find_one({"owner": owner, "name": name})
    if repo is None:
        logger.info("Repo not found in database, creating...")
        repo = {
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "owner": owner,
            "name": name,
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

    existing_months = {(m["month"].year, m["month"].month) for m in repo["stars"]}
    # TODO: Implement count stars

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

    repo["updated_at"] = datetime.now(timezone.utc)
    with pymongo.MongoClient(CONFIG["mongodb"]["url"]) as client:
        client.gfibot.repos.replace_one(
            {"owner": owner, "name": name}, repo, upsert=True
        )
    return repo


def update_issues(fetcher: RepoFetcher, repo: Dict[str, Any]) -> None:
    with pymongo.MongoClient(CONFIG["mongodb"]["url"]) as client:
        existing = client.gfibot.repos.issues.count_documents(
            {"name": fetcher.name, "owner": fetcher.owner}
        )

    since = repo["repo_created_at"] if existing == 0 else repo["updated_at"]
    updated_issues = fetcher.get_issues(since)
    logger.info(
        "%d issues (%d updated), rate remaining %s",
        existing + len(updated_issues),
        len(updated_issues),
        fetcher.gh.rate_limiting,
    )

    with pymongo.MongoClient(CONFIG["mongodb"]["url"]) as client:
        for issue in updated_issues:
            client.gfibot.repos.issues.replace_one(
                {
                    "owner": fetcher.owner,
                    "name": fetcher.name,
                    "number": issue["number"],
                },
                issue,
                upsert=True,
            )


def update(token: str, owner: str, name: str) -> None:
    repo_fetcher = RepoFetcher(token, owner, name)
    repo = update_repo(repo_fetcher)
    update_issues(repo_fetcher, repo)


if __name__ == "__main__":
    for i, project in enumerate(CONFIG["gfibot"]["projects"]):
        owner, name = project.split("/")
        update(TOKENS[i % len(TOKENS)], owner, name)
    logger.info("Done!")
