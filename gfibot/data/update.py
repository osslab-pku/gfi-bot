import re
import logging
import argparse
import numpy as np

from typing import List, Dict, Any, Iterable, Tuple
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from gfibot import CONFIG, TOKENS
from gfibot.check_tokens import check_tokens
from gfibot.collections import *
from gfibot.data.graphql import UserFetcher
from gfibot.data.rest import RepoFetcher, logger as rest_logger


logger = logging.getLogger(__name__)


def count_by_month(dates: List[datetime]) -> List[Repo.MonthCount]:
    counts = Counter(map(lambda d: (d.year, d.month), dates))
    return sorted(
        [
            Repo.MonthCount(
                month=datetime(year=y, month=m, day=1, tzinfo=timezone.utc), count=c
            )
            for (y, m), c in counts.items()
        ],
        key=lambda k: k["month"],
    )


def match_issue_numbers(text: str) -> List[int]:
    """
    Match close issue text in a pull request, as documented in:
    https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue
    """
    numbers = []
    regex = r"(close[sd]?|fix(es|ed)?|resolve[sd]?) \#(\d+)"
    for _, _, number in re.findall(regex, text.lower()):
        numbers.append(int(number))
    return numbers


def update_repo_info(fetcher: RepoFetcher) -> Repo:
    logger.info("Updating repo: %s/%s", fetcher.owner, fetcher.name)
    repo = Repo.objects(owner=fetcher.owner, name=fetcher.name)
    if repo.count() == 0:
        logger.info("Repo not found in database, creating...")
        repo = Repo(
            created_at=datetime.now(timezone.utc),
            updated_at=None,
            owner=fetcher.owner,
            name=fetcher.name,
        )
    else:
        repo = repo.first()

    for k, v in fetcher.get_stats().items():
        if k == "languages":
            v = [Repo.LanguageCount(language=k2, count=v2) for k2, v2 in v.items()]
        setattr(repo, k, v)
    logger.info("Repo stats updated, rate remaining %s", fetcher.get_rate_limit())
    return repo


def update_stars(fetcher: RepoFetcher, since: datetime) -> List[Dict[str, Any]]:
    stars = fetcher.get_stars(since)
    logger.info(
        "%d stars updated, rate remaining %s", len(stars), fetcher.get_rate_limit()
    )
    for star in stars:
        RepoStar.objects(
            owner=fetcher.owner, name=fetcher.name, user=star["user"]
        ).upsert_one(**star)
    return stars


def update_commits(fetcher: RepoFetcher, since: datetime) -> List[Dict[str, Any]]:
    commits = fetcher.get_commits(since)
    logger.info(
        "%d commits updated, rate remaining %s",
        len(commits),
        fetcher.get_rate_limit(),
    )
    for commit in commits:
        RepoCommit.objects(
            owner=fetcher.owner, name=fetcher.name, sha=commit["sha"]
        ).upsert_one(**commit)
    return commits


def update_issues(fetcher: RepoFetcher, since: datetime) -> List[Dict[str, Any]]:
    issues = fetcher.get_issues(since)
    logger.info(
        "%d issues updated, rate remaining %s",
        len(issues),
        fetcher.get_rate_limit(),
    )
    for issue in issues:
        RepoIssue.objects(
            owner=fetcher.owner, name=fetcher.name, number=issue["number"]
        ).upsert_one(**issue)
    return issues


def update_repo_stats(repo: Repo):
    owner, name = repo.owner, repo.name
    all_issues: List[RepoIssue] = list(RepoIssue.objects(owner=owner, name=name))

    # Median issue close time
    closed_t = [
        (i.closed_at - i.created_at).total_seconds()
        for i in all_issues
        if i.state == "closed" and not i.is_pull
    ]
    repo.median_issue_close_time = np.median(closed_t) if len(closed_t) > 0 else None

    # Monthly data
    repo.monthly_stars = count_by_month(
        RepoStar.objects(owner=owner, name=name).scalar("starred_at")
    )
    repo.monthly_commits = count_by_month(
        RepoCommit.objects(owner=owner, name=name).scalar("committed_at")
    )
    repo.monthly_issues = count_by_month(
        [i.created_at for i in all_issues if not i.is_pull]
    )
    repo.monthly_pulls = count_by_month([i.created_at for i in all_issues if i.is_pull])


def locate_resolved_issues(
    fetcher: RepoFetcher, since: datetime
) -> List[Dict[str, Any]]:
    all_issues: Dict[int, RepoIssue] = {
        i.number: i
        for i in RepoIssue.objects(
            owner=fetcher.owner, name=fetcher.name, is_pull=False, closed_at__gte=since
        )
    }
    all_commits: List[RepoCommit] = sorted(
        RepoCommit.objects(owner=fetcher.owner, name=fetcher.name),
        key=lambda c: c.authored_at,
    )
    closed_nums = set(map(lambda i: i.number, all_issues.values()))
    logger.info("%d newly closed issues since %s", len(all_issues), since)

    resolved = defaultdict(
        lambda: {
            "owner": fetcher.owner,
            "name": fetcher.name,
            "number": None,
            "created_at": None,
            "resolved_at": None,
            "resolver": None,
            "resolved_in": None,
            "resolver_commit_num": None,
            "events": [],
        }
    )

    # Note that, we first get possible issue resolver *using commits*,
    #   then we get possible resolver using PRs.
    # In this way, resolver obtained through PRs has higher priority.
    # Also, all commits and issues are sorted by date, so resolver from later commits
    #   and later PRs have higher priority.
    author2commits = defaultdict(list)
    for c in all_commits:
        author2commits[c.author].append(c)
    for c in all_commits:
        if c.author is None:
            continue
        commits_before = set()
        for c2 in author2commits[c.author]:
            if c2.authored_at < c.authored_at:
                commits_before.add(c2.sha)
        for num in match_issue_numbers(c.message):
            if num not in closed_nums:
                continue
            logger.debug(
                "Issue #%d resolved in %s by %s (%d prior commits)",
                num,
                c.sha,
                c.author,
                len(commits_before),
            )
            resolved[num]["number"] = num
            resolved[num]["resolver"] = c.author
            resolved[num]["resolved_in"] = c.sha
            resolved[num]["resolver_commit_num"] = len(commits_before)
    logger.info("%d issues found to be resolved by commits", len(resolved))

    for issue in all_issues.values():
        t1 = issue.closed_at - timedelta(minutes=1)
        t2 = issue.closed_at + timedelta(minutes=1)
        prs: List[RepoIssue] = list(
            RepoIssue.objects(
                owner=fetcher.owner,
                name=fetcher.name,
                is_pull=True,
                merged_at__gt=t1,
                merged_at__lt=t2,
            )
        )
        if len(prs) > 0:
            logger.debug(
                "Candidate PRs %s for issue %d, rate remaining = %s",
                [pr.number for pr in prs],
                issue.number,
                fetcher.get_rate_limit(),
            )
        for pr in prs:
            pr_details = fetcher.get_pull_detail(pr.number)
            text = [pr.title, pr.body, *pr_details["comments"]]
            text = "\n".join([t for t in text if t is not None])
            commits_before = set()
            for c in author2commits[pr.user]:
                if c.authored_at < pr.merged_at and c.sha not in pr_details["commits"]:
                    commits_before.add(c.sha)
            if issue.number in match_issue_numbers(text):
                logger.debug(
                    "Issue #%d resolved in #%d by %s (%d prior commits)",
                    issue.number,
                    pr.number,
                    pr.user,
                    len(commits_before),
                )
                resolved[issue.number]["number"] = issue.number
                resolved[issue.number]["resolver"] = pr.user
                resolved[issue.number]["resolved_in"] = pr.number
                resolved[issue.number]["resolver_commit_num"] = len(commits_before)
    logger.info("%d issues found to be resolved by commits/PRs", len(resolved))

    for num in resolved.keys():
        resolved[num]["created_at"] = all_issues[num].created_at
        resolved[num]["resolved_at"] = all_issues[num].closed_at
    return list(resolved.values())


def update_resolved_issues(
    fetcher: RepoFetcher, since: datetime
) -> List[Dict[str, Any]]:
    """Fetch data for issues that will be used for RecGFI training."""
    resolved_issues = locate_resolved_issues(fetcher, since)
    for resolved_issue in resolved_issues:
        logger.debug(
            "Fetching details for resolved issue #%d, rate remaining = %s",
            resolved_issue["number"],
            fetcher.get_rate_limit(),
        )
        for event in fetcher.get_issue_detail(resolved_issue["number"])["events"]:
            resolved_issue["events"].append(IssueEvent(**event))
    for resolved_issue in resolved_issues:
        ResolvedIssue.objects(
            owner=fetcher.owner, name=fetcher.name, number=resolved_issue["number"]
        ).upsert_one(**resolved_issue)
    return resolved_issues


def update_open_issues(fetcher: RepoFetcher, nums: List[int], since: datetime):
    """Fetch data for all new open issues"""
    query = Q(name=fetcher.name, owner=fetcher.owner)
    open_issues = RepoIssue.objects(
        query & Q(is_pull=False, state="open", number__in=nums)
    )
    logger.info("%d open issues updated since %s", open_issues.count(), since)
    for issue in open_issues:
        existing = OpenIssue.objects(query & Q(number=issue.number))
        if existing.count() > 0:
            open_issue = existing.first()
        else:
            open_issue = OpenIssue(
                name=fetcher.name,
                owner=fetcher.owner,
                number=issue.number,
                created_at=issue.created_at,
                updated_at=since,
            )
        logger.debug(
            "Fetching details for open issue #%d, rate remaining = %s",
            issue.number,
            fetcher.get_rate_limit(),
        )
        open_issue.events = [
            IssueEvent(**e) for e in fetcher.get_issue_detail(issue.number)["events"]
        ]
        open_issue.save()
    closed_issue_nums = list(
        RepoIssue.objects(query & Q(is_pull=False, state="closed")).scalar("number")
    )
    OpenIssue.objects(query & Q(number__in=closed_issue_nums)).delete()


def _update_user_issues(user: User, res: Dict[str, Any]) -> None:
    """Update issues for a user."""
    user.issues = [
        User.Issue(
            owner=issue["repository"]["nameWithOwner"].split("/")[0],
            name=issue["repository"]["nameWithOwner"].split("/")[1],
            repo_stars=issue["repository"]["stargazerCount"],
            state=issue["state"],
            number=issue["number"],
            created_at=issue["createdAt"],
        )
        for issue in res["nodes"]
    ]


def _update_user_pulls(user: User, res: Dict[str, Any]) -> None:
    """Update pull request contributions for a user."""
    user.pulls = [
        User.Pull(
            owner=pr["pullRequest"]["repository"]["nameWithOwner"].split("/")[0],
            name=pr["pullRequest"]["repository"]["nameWithOwner"].split("/")[1],
            repo_stars=pr["pullRequest"]["repository"]["stargazerCount"],
            state=pr["pullRequest"]["state"],
            created_at=pr["pullRequest"]["createdAt"],
            number=pr["pullRequest"]["number"],
        )
        for pr in res["nodes"]
    ]


def _update_user_commits(user: User, res: Dict[str, Any]) -> None:
    """Update commits for a user."""
    user.commits = []
    for commit_contrib in res:
        owner = commit_contrib["repository"]["nameWithOwner"].split("/")[0]
        name = commit_contrib["repository"]["nameWithOwner"].split("/")[1]
        repo_stars = commit_contrib["repository"]["stargazerCount"]

        for contrib in commit_contrib["contributions"]["nodes"]:
            user.commit_contributions.append(
                User.CommitContribution(
                    owner=owner,
                    name=name,
                    repo_stars=repo_stars,
                    commit_count=contrib["commitCount"],
                    created_at=contrib["occurredAt"],
                )
            )


def _update_user_reviews(user: User, res: Dict[str, Any]) -> None:
    """Update reviews for a user."""
    user.pull_reviews = [
        User.Review(
            owner=review["repository"]["nameWithOwner"].split("/")[0],
            name=review["repository"]["nameWithOwner"].split("/")[1],
            repo_stars=review["repository"]["stargazerCount"],
            created_at=review["pullRequestReview"]["createdAt"],
            state=review["pullRequestReview"]["state"],
            number=review["pullRequestReview"]["pullRequest"]["number"],
        )
        for review in res["nodes"]
    ]


def _update_user_meta(user: User, res: Dict[str, Any]) -> None:
    """Update meta data for a user."""
    user.name = res["name"]


def _update_user_query(rate_state: dict, res: Dict[str, Any]) -> None:
    rate_state["remaining"] = res["rateLimit"]["remaining"]
    rate_state["resetAt"] = res["rateLimit"]["resetAt"]
    if "cost" not in rate_state:
        rate_state["cost"] = 0
    rate_state["cost"] += res["rateLimit"]["cost"]


def update_user(token: str, login: str) -> None:
    """Fetch data for a user"""
    # does the user exist?
    user = User.objects(login=login).first()
    time_now = datetime.utcnow()
    if user is None:
        user = User(login=login, _created_at=time_now)
        since = datetime(2008, 1, 1)  # GitHub was launched in 2008
    else:
        since = user._updated_at

    user._updated_at = time_now

    rate_state = {}

    fetcher = UserFetcher(
        token=token,
        login=login,
        since=since,
        callbacks={
            "query": lambda res: _update_user_query(rate_state, res),
            "user": lambda res: _update_user_meta(user, res),
            "issues": lambda res: _update_user_issues(user, res),
            "pullRequestContributions": lambda res: _update_user_pulls(user, res),
            "commitContributionsByRepository": lambda res: _update_user_commits(
                user, res
            ),
            "pullRequestReviewContributions": lambda res: _update_user_reviews(
                user, res
            ),
        },
    )
    try:
        fetcher.fetch()
        user.save()
        logger.info(
            "User %s updated from %s to %s, ratelimit cost=%d remaining=%d",
            login,
            since.strftime("%Y-%m-%dT%H:%M:%SZ"),
            user._updated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            rate_state["cost"],
            rate_state["remaining"],
        )
    except Exception as e:
        logger.error("Failed to update user %s", login)
        logger.exception(e)


def update_repo(token: str, owner: str, name: str) -> None:
    """Update all information of a repository for RecGFI training"""
    fetcher = RepoFetcher(token, owner, name)

    repo = update_repo_info(fetcher)
    if repo.updated_at is None:
        since = repo.repo_created_at
    else:
        since = repo.updated_at
    repo.updated_at = datetime.now(timezone.utc)

    logger.info("Update stars, commits, and issues since %s", since)
    stars = update_stars(fetcher, since)
    commits = update_commits(fetcher, since)
    issues = update_issues(fetcher, since)

    update_repo_stats(repo)

    repo.save()

    resolved_issues = update_resolved_issues(fetcher, since)

    open_issue_nums = [
        i["number"] for i in issues if i["state"] == "open" and not i["is_pull"]
    ]
    update_open_issues(fetcher, open_issue_nums, since)

    all_users = set([owner])
    for commit in commits:
        all_users.add(commit["author"])
    for issue in issues:
        all_users.add(issue["user"])
    for resolved in resolved_issues:
        all_users.add(resolved["resolver"])
        for event in resolved["events"]:
            all_users.add(event["actor"])
            if "assignee" in event:
                all_users.add(event["assignee"])
            if "commenter" in event:
                all_users.add(event["commenter"])
    logger.info("%d users associated with %s/%s", len(all_users), owner, name)

    for user in all_users:
        update_user(token, user)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
        rest_logger.setLevel(logging.DEBUG)

    # run check_tokens before update
    failed_tokens = check_tokens()
    valid_tokens = list(set(TOKENS) - failed_tokens)

    for i, project in enumerate(CONFIG["gfibot"]["projects"]):
        owner, name = project.split("/")
        update_repo(valid_tokens[i % len(valid_tokens)], owner, name)

    logger.info("Done!")
