import os
import re
import logging
import argparse
import mongoengine
import numpy as np
import multiprocessing as mp

from typing import List, Dict, Set, Any, Optional
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from gfibot import CONFIG, TOKENS
from gfibot.check_tokens import check_tokens
from gfibot.collections import *
from gfibot.data.graphql import UserFetcher
from gfibot.data.rest import RepoFetcher, logger as rest_logger
from gfibot.data.features.temporal import count_by_month
from gfibot.data.features.repo_features import (
    compute_issue_close_time_median,
    detect_issue_resolutions,
)


logger = logging.getLogger(__name__)




def _match_issue_numbers(text: str) -> List[int]:
    """
    Match close issue text in a pull request, as documented in:
    https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue
    """
    numbers = []
    regex = r"(close[sd]?|fix(es|ed)?|resolve[sd]?) \#(\d+)"
    for _, _, number in re.findall(regex, text.lower()):
        numbers.append(int(number))
    return numbers


def _update_repo_info(fetcher: RepoFetcher) -> Repo:
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
    logger.info("Repo stats updated, rate = %s", fetcher.rate)
    return repo


def _update_stars(fetcher: RepoFetcher, since: datetime) -> List[Dict[str, Any]]:
    stars = fetcher.get_stars(since)
    logger.info("%d stars updated, rate = %s", len(stars), fetcher.rate)
    for star in stars:
        RepoStar.objects(
            owner=fetcher.owner, name=fetcher.name, user=star["user"]
        ).upsert_one(**star)
    return stars


def _update_commits(fetcher: RepoFetcher, since: datetime) -> List[Dict[str, Any]]:
    commits = fetcher.get_commits(since)
    logger.info(
        "%d commits updated, rate = %s",
        len(commits),
        fetcher.rate,
    )
    for commit in commits:
        RepoCommit.objects(
            owner=fetcher.owner, name=fetcher.name, sha=commit["sha"]
        ).upsert_one(**commit)
    return commits


def _update_issues(fetcher: RepoFetcher, since: datetime) -> List[Dict[str, Any]]:
    issues = fetcher.get_issues(since)
    logger.info(
        "%d issues updated, rate = %s",
        len(issues),
        fetcher.rate,
    )
    for issue in issues:
        RepoIssue.objects(
            owner=fetcher.owner, name=fetcher.name, number=issue["number"]
        ).upsert_one(**issue)
    return issues


def _update_repo_stats(repo: Repo):
    owner, name = repo.owner, repo.name
    all_issues: List[RepoIssue] = list(RepoIssue.objects(owner=owner, name=name))
    all_stars = list(RepoStar.objects(owner=owner, name=name).scalar("starred_at"))
    all_commits = list(RepoCommit.objects(owner=owner, name=name).scalar("committed_at"))

    # Compute median issue close time using extracted pure function
    repo.median_issue_close_time = compute_issue_close_time_median(all_issues)

    # Monthly data
    repo.monthly_stars = count_by_month(all_stars)
    repo.monthly_commits = count_by_month(all_commits)
    repo.monthly_issues = count_by_month(
        [i.created_at for i in all_issues if not i.is_pull]
    )
    repo.monthly_pulls = count_by_month(
        [i.created_at for i in all_issues if i.is_pull]
    )


def _locate_resolved_issues(
    fetcher: RepoFetcher, since: datetime
) -> List[Dict[str, Any]]:
    """Locate resolved issues by fetching data and detecting resolutions."""
    # STEP 1: Fetch issues and commits from database
    all_issues_db: Dict[int, RepoIssue] = {
        i.number: i
        for i in RepoIssue.objects(
            owner=fetcher.owner, name=fetcher.name, is_pull=False, closed_at__gte=since
        )
    }
    all_commits_db: List[RepoCommit] = sorted(
        RepoCommit.objects(owner=fetcher.owner, name=fetcher.name),
        key=lambda c: c.authored_at,
    )
    logger.info("%d newly closed issues since %s", len(all_issues_db), since)

    # STEP 2: Fetch PR details from API
    prs_dict = {}
    for issue in all_issues_db.values():
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
                "Candidate PRs %s for issue %d, rate = %s",
                [pr.number for pr in prs],
                issue.number,
                fetcher.rate,
            )
        for pr in prs:
            pr_details = fetcher.get_pull_detail(pr.number)
            prs_dict[pr.number] = {
                "user": pr.user,
                "title": pr.title,
                "body": pr.body,
                "merged_at": pr.merged_at,
                "comments": pr_details.get("comments", []),
                "commits": pr_details.get("commits", []),
            }

    # STEP 3: Use pure function to detect resolutions
    resolved_issues = detect_issue_resolutions(
        issues_dict=all_issues_db,
        commits_list=all_commits_db,
        prs_dict=prs_dict if prs_dict else None,
    )

    logger.info("%d issues found to be resolved", len(resolved_issues))
    return resolved_issues


def _update_resolved_issues(
    fetcher: RepoFetcher, since: datetime
) -> List[Dict[str, Any]]:
    """Fetch data for issues that will be used for RecGFI training."""
    resolved_issues = _locate_resolved_issues(fetcher, since)
    for resolved_issue in resolved_issues:
        logger.debug(
            "Fetching details for resolved issue #%d, rate = %s",
            resolved_issue["number"],
            fetcher.rate,
        )
        for event in fetcher.get_issue_detail(resolved_issue["number"])["events"]:
            resolved_issue["events"].append(IssueEvent(**event))
    for resolved_issue in resolved_issues:
        ResolvedIssue.objects(
            owner=fetcher.owner, name=fetcher.name, number=resolved_issue["number"]
        ).upsert_one(**resolved_issue)
    return resolved_issues


def _update_open_issues(fetcher: RepoFetcher, nums: List[int], since: datetime):
    """Fetch data for all new open issues"""
    query = Q(name=fetcher.name, owner=fetcher.owner)
    repo_open_issues = RepoIssue.objects(
        query & Q(is_pull=False, state="open", number__in=nums)
    )
    logger.info("%d open issues updated since %s", repo_open_issues.count(), since)

    open_issues = []
    for issue in list(repo_open_issues):
        existing = OpenIssue.objects(query & Q(number=issue.number))
        if existing.count() > 0:
            open_issue = existing.first()
            open_issue.updated_at = datetime.utcnow()
        else:
            open_issue = OpenIssue(
                name=fetcher.name,
                owner=fetcher.owner,
                number=issue.number,
                created_at=issue.created_at,
                updated_at=datetime.utcnow(),
            )

        logger.debug(
            "Fetching details for open issue #%d, rate = %s",
            issue.number,
            fetcher.rate,
        )
        open_issue.events = [
            IssueEvent(**e) for e in fetcher.get_issue_detail(issue.number)["events"]
        ]
        open_issue.save()
        open_issues.append(open_issue)

    # Delete issues that are closed now
    closed_issue_nums = list(
        RepoIssue.objects(query & Q(is_pull=False, state="closed")).scalar("number")
    )
    OpenIssue.objects(query & Q(number__in=closed_issue_nums)).delete()

    return open_issues


def _find_users(
    owner: str,
    name: str,
    commits: list,
    issues: list,
    open_issues: list,
    resolved_issues: list,
) -> Set[str]:
    all_users = set([owner])
    issue_nums = set(i["number"] for i in open_issues + resolved_issues)
    for issue in issues:
        if issue["number"] in issue_nums:
            all_users.add(issue["user"])
    """
    for resolved in resolved_issues:
        all_users.add(resolved["resolver"])
        for event in resolved["events"]:
            all_users.add(event["actor"])
            if "assignee" in event:
                all_users.add(event["assignee"])
            if "commenter" in event:
                all_users.add(event["commenter"])
    for open in open_issues:
        for event in open["events"]:
            all_users.add(event["actor"])
            if "assignee" in event:
                all_users.add(event["assignee"])
            if "commenter" in event:
                all_users.add(event["commenter"])
    """
    if None in all_users:
        all_users.remove(None)
    logger.info("%d users associated with %s/%s", len(all_users), owner, name)
    return all_users


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
    rate_state["cost"] += res["rateLimit"]["cost"]


def update_user(token: str, login: str) -> int:
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

    # Fix 'rate limit exceed' in CI environment
    _is_ci = os.environ.get("CI", "")
    if _is_ci:
        logger.info("Running in CI environment, overriding 'since' date")
        since = time_now - timedelta(days=7)

    rate_state = {"cost": 0}

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

    return rate_state["cost"]


# def update_gfi_repo_add_query(owner: str, name: str) -> None:
#     """TODO: Remove this function after we have a better logging system"""
#     GfiQueries.objects(Q(owner=owner) & Q(name=name)).update_one(
#         set__is_pending=False,
#         set__is_finished=True,
#         set__is_updating=False,
#         set___finished_at=datetime.now(timezone.utc),
#     )


def update_repo(
    token: str, owner: str, name: str, user_github_login: Optional[str] = None
) -> None:
    """Update all information of a repository for RecGFI training

    Args:
        token (str): A GitHub access token
        owner (str): repository owner
        name (str): repository name
        user_github_login (Optional[str], optional):
            If this function is called from backend, indicate which user intiated this update.
            Defaults to None.
    """
    if update_in_progress(owner, name, GitHubFetchLog):
        logger.info("%s/%s is already being updated, skipping", owner, name)
        return

    log = GitHubFetchLog(
        owner=owner,
        name=name,
        pid=os.getpid(),
        update_begin=datetime.now(timezone.utc),
        user_github_login=user_github_login,
    )
    log.save()

    fetcher = RepoFetcher(token, owner, name)

    logger.info("Fetching repo %s/%s", owner, name)
    repo = _update_repo_info(fetcher)

    if repo.updated_at is None:
        since = repo.repo_created_at
    else:
        since = repo.updated_at
    repo.updated_at = datetime.now(timezone.utc)

    logger.info("Update stars, commits, and issues since %s", since)
    stars = _update_stars(fetcher, since)
    commits = _update_commits(fetcher, since)
    issues = _update_issues(fetcher, since)

    log.updated_stars = len(stars)
    log.updated_issues = len(issues)
    log.updated_commits = len(commits)
    log.rate = fetcher.rate_consumed
    log.rate_repo_stat = fetcher.rate_consumed
    log.save()

    resolved_issues = _update_resolved_issues(fetcher, since)
    log.updated_resolved_issues = len(resolved_issues)
    log.rate = fetcher.rate_consumed
    log.rate_resolved_issue = fetcher.rate_consumed - log.rate_repo_stat
    log.save()

    # update_gfi_repo_add_query(owner, name)

    open_issue_nums = [
        i["number"] for i in issues if i["state"] == "open" and not i["is_pull"]
    ]
    open_issues = _update_open_issues(fetcher, open_issue_nums, since)
    log.updated_open_issues = len(open_issues)
    log.rate = fetcher.rate_consumed
    log.rate_open_issue = (
        fetcher.rate_consumed - log.rate_repo_stat - log.rate_resolved_issue
    )
    log.save()

    # update_gfi_repo_add_query(owner, name)

    all_users = _find_users(owner, name, commits, issues, open_issues, resolved_issues)
    log.rate_user = 0
    for user in all_users:
        if user is None or type(user) != str:
            continue
        log.rate_user += update_user(token, user)
    log.updated_users = len(all_users)
    log.rate = log.rate + log.rate_user
    log.update_end = datetime.now(timezone.utc)
    log.save()

    _update_repo_stats(repo)
    repo.save()
    logger.info("Finished updating for %s/%s since %s", owner, name, since)


def update_under_one_token(token: str, repos: List[str]) -> None:
    # Reconnect in a new process
    mongoengine.connect(
        CONFIG["mongodb"]["db"],
        host=CONFIG["mongodb"]["url"],
        tz_aware=True,
        uuidRepresentation="standard",
    )

    logging.info("token = %s, repos = %s", token[0:6], repos)
    for repo in repos:
        owner, name = repo.split("/")
        update_repo(token, owner, name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--nprocess", type=int, default=mp.cpu_count())
    parser.add_argument("--repos", type=str, default="")
    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
        rest_logger.setLevel(logging.DEBUG)
    if args.repos == "":
        repos = CONFIG["gfibot"]["projects"]
    else:
        repos = args.repos.split(",")

    # run check_tokens before update
    failed_tokens = check_tokens(TOKENS)
    valid_tokens = list(set(TOKENS) - failed_tokens)

    logger.info("Data update started at {}".format(datetime.now()))

    params = defaultdict(list)
    for i, project in enumerate(repos):
        params[valid_tokens[i % len(valid_tokens)]].append(project)
    with mp.Pool(min(args.nprocess, len(valid_tokens))) as pool:
        pool.starmap(update_under_one_token, params.items())

    logger.info("Data update finished at {}".format(datetime.now()))


if __name__ == "__main__":
    main()
