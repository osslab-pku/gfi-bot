import time
import logging

from typing import *
from datetime import datetime, timezone
from calendar import monthrange
from dateutil.parser import parse as parse_date
from github import Github
from github import RateLimitExceededException, UnknownObjectException
from github.GithubObject import NotSet


T = TypeVar("T")
logger = logging.getLogger(__name__)


def get_page_num(per_page: int, total_count: int) -> int:
    """Calculate total number of pages given page size and total number of items"""
    assert per_page > 0 and total_count >= 0
    if total_count % per_page == 0:
        return total_count // per_page
    return total_count // per_page + 1


def request_github(
    gh: Github, gh_func: Callable[..., T], params: Tuple = (), default: Any = None
) -> Optional[T]:
    """
    This is a wrapper to ensure that any rate-consuming interactions with GitHub
      have proper exception handling.
    """
    for _ in range(0, 3):  # Max retry 3 times
        try:
            data = gh_func(*params)
            return data
        except RateLimitExceededException as ex:
            logger.info("{}: {}".format(type(ex), ex))
            sleep_time = gh.rate_limiting_resettime - time.time() + 10
            logger.info("Rate limit reached, wait for {} seconds...".format(sleep_time))
            time.sleep(max(1.0, sleep_time))
        except UnknownObjectException as ex:
            logger.error("{}: {}".format(type(ex), ex))
            break
        except Exception as ex:
            logger.error("{}: {}".format(type(ex), ex))
            time.sleep(5)
    return default


def get_month_interval(date: datetime) -> Tuple[datetime, datetime]:
    if date.tzinfo is None:
        logger.warning("date is not timezone aware: {}".format(date))
        date = date.replace(tzinfo=timezone.utc)
    date = date.astimezone(timezone.utc)
    since = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    until = date.replace(
        day=monthrange(date.year, date.month)[1],
        hour=23,
        minute=59,
        second=59,
        microsecond=999999,
    )
    return since, until


class RepoFetcher(object):
    def __init__(self, token: str, owner: str, name: str):
        self.gh = Github(token)
        self.gh.per_page = 100  # minimize rate limit consumption
        self.repo = request_github(self.gh, lambda: self.gh.get_repo(f"{owner}/{name}"))
        self.owner = self.repo.owner.login
        self.name = self.repo.name

    def get_stats(self) -> dict[str, Any]:
        return request_github(
            self.gh,
            lambda: {
                "owner": self.repo.owner.login,
                "name": self.repo.name,
                "language": self.repo.language,
                "repo_created_at": self.repo.created_at.astimezone(timezone.utc),
            },
        )

    def get_commits_in_month(self, date: datetime) -> dict[str, Any]:
        since, until = get_month_interval(date)
        return request_github(
            self.gh,
            lambda: self.repo.get_commits(since=since, until=until).totalCount,
            default=0,
        )

    def get_commits(self, since: datetime) -> List[dict[str, Any]]:
        results = []
        commits = request_github(
            self.gh, lambda: self.repo.get_commits(since=since), default=[]
        )
        page_num = get_page_num(self.gh.per_page, commits.totalCount)
        for p in range(0, page_num):
            logger.debug(
                "commit page %d/%d, rate %s", p, page_num, self.gh.rate_limiting
            )
            for commit in request_github(self.gh, commits.get_page, (p,), []):
                try:
                    author = commit.author.login
                except:
                    author = None
                try:
                    committer = commit.committer.login
                except:
                    committer = None
                results.append(
                    {
                        "owner": self.owner,
                        "name": self.name,
                        "sha": commit.sha,
                        "author": author,
                        "authored_at": commit.commit.author.date.astimezone(
                            timezone.utc
                        ),
                        "committer": committer,
                        "committed_at": commit.commit.committer.date.astimezone(
                            timezone.utc
                        ),
                        "message": commit.commit.message,
                    }
                )
        return results

    def get_issues(self, since: datetime) -> List[dict[str, Any]]:
        results = []
        issues = request_github(
            self.gh,
            lambda: self.repo.get_issues(since=since, direction="asc", state="all"),
            default=[],
        )
        page_num = get_page_num(self.gh.per_page, issues.totalCount)
        for p in range(0, page_num):
            logger.debug(
                "issue page %d/%d, rate %s", p, page_num, self.gh.rate_limiting
            )
            for issue in request_github(self.gh, issues.get_page, (p,), []):
                if issue.state == "closed":
                    closed_at = issue.closed_at.astimezone(timezone.utc)
                else:
                    closed_at = None
                is_pull = issue._pull_request != NotSet  # avoid rate limit
                if is_pull:
                    merged_at = issue.pull_request.raw_data["merged_at"]
                    if merged_at is not None:
                        merged_at = parse_date(merged_at).astimezone(timezone.utc)
                else:
                    merged_at = None
                results.append(
                    {
                        "owner": self.owner,
                        "name": self.name,
                        "number": issue.number,
                        "user": issue.user.login,
                        "state": issue.state,
                        "created_at": issue.created_at.astimezone(timezone.utc),
                        "closed_at": closed_at,
                        "is_pull": is_pull,
                        "merged_at": merged_at,
                    }
                )
        return results
