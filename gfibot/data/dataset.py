import re
import nltk
import logging
import textstat
import numpy as np

from collections import Counter
from gfibot.collections import *
from mongoengine.queryset.visitor import Q

logger = logging.getLogger(__name__)


def count_code_snippets(s: str) -> int:
    p = re.compile(r"```.+?```", flags=re.S)
    if s is None:
        return 0
    return len(p.findall(s))


def delete_code_snippets(s: str) -> str:
    if s is None:
        return ""
    p = re.compile(r"```.+?```", flags=re.S)
    s = p.sub("", s)
    # return " ".join(s.split())
    return s


def count_urls(s: str) -> int:
    if s is None:
        return 0
    p = re.compile(r"http[:/\w\.]+")
    lst = list(
        filter(  # do not count images, this will be done in count_imgs()
            lambda s2: not (
                s2.endswith("jpg") or s2.endswith("jpeg") or s2.endswith("png")
            ),
            p.findall(s),
        )
    )
    return len(lst)


def delete_urls(s: str) -> str:
    if s == None:
        return ""
    p = re.compile(r"http[:/\w\.]+")
    s = p.sub("", s)
    # return " ".join(s.split())
    return s


def count_imgs(s: str) -> int:
    if s is None:
        return 0
    p = re.compile(r"http[:/\w\.]+")
    lst = list(
        filter(
            lambda s2: s2.endswith("jpg") or s2.endswith("jpeg") or s2.endswith("png"),
            p.findall(s),
        )
    )
    return len(lst)


def count_text_len(s: str) -> int:
    if s == None:
        return 0
    return len(s.split())


def get_categorized_labels(labels: List[str]) -> Dataset.LabelCategory:
    keyword_rules = {
        "bug": ["bug"],
        "feature": ["feature"],
        "test": ["test", "testing"],
        "build": ["ci", "build"],
        "doc": ["doc", "document", "documentation"],
        "coding": ["code", "coding", "program", "programming"],
        "enhance": ["enhance", "enhancement"],
        "gfi": [
            "easy",
            "starter",
            "newbie",
            "beginner",
            "starter",
            "minor",
            "novice",
            ("good", "first"),
            ("low", "fruit"),
            ("effort", "low"),
            ("first", "time"),
            ("first", "timer"),
            ("first", "pr"),
            ("up", "for", "grab"),
        ],
        "medium": ["medium", "intermediate"],
        "major": [
            "important",
            "major",
            "breaking",
            "difficult",
            "hard",
            "core",
            "serious",
            ("priority", "p1"),
            ("priority", "high"),
            ("priority", "critical"),
        ],
        "triaged": [
            "triaged",
            "triage",
            "progress",
            "haspr",
            "fixed",
            "wontfix",
            ("ha", "pr"),
            ("ha", "fix"),
        ],
        "untriaged": [
            "untriaged",
            ("need", "triage"),
            ("needed", "triage"),
            ("no", "triage"),
        ],
    }

    label_cat = Counter()
    lemmatizer = nltk.stem.WordNetLemmatizer()
    for label in labels:
        words = re.compile(r"\w+").findall(label.lower().replace("_", " "))
        words = [lemmatizer.lemmatize(w) for w in words]
        for cat, rules in keyword_rules.items():
            match = 0
            for rule in rules:
                if isinstance(rule, (tuple, list)):
                    if all(word in words for word in rule):
                        match = 1
                elif rule in words:
                    match = 1
                elif any(rule in w for w in words):
                    match = 1
            label_cat[cat] += match
    return Dataset.LabelCategory(**label_cat)


def get_user_data(owner: str, name: str, user: str, t: datetime) -> Dataset.UserFeature:
    """Get user data before a certain time t"""

    if user == "ghost":  # The name of deleted GitHub account
        return Dataset.UserFeature(
            name=user,
            n_commits=0,
            n_issues=0,
            n_pulls=0,
            resolver_commits=[],
        )

    # "web-flow" is a special account for all web commits (merge/revert/edit/etc...) made on GitHub
    usrcmts: List[RepoCommit] = list(
        RepoCommit.objects(
            Q(owner=owner, name=name, authored_at__lte=t, committed_at__lte=t)
            & (Q(committer=user) | Q(author=user, committer="web-flow"))
        )
    )

    issue_query = Q(
        owner=owner,
        name=name,
        user=user,
        created_at__lte=t,
    )
    usriss: List[RepoIssue] = list(RepoIssue.objects(issue_query & Q(is_pull=False)))
    usrpulls: List[RepoIssue] = list(RepoIssue.objects(issue_query & Q(is_pull=True)))

    usriss_resolved: List[ResolvedIssue] = list(
        ResolvedIssue.objects(
            owner=owner,
            name=name,
            number__in=[
                i.number for i in usriss if i.state == "closed" and i.closed_at <= t
            ],
        )
    )
    usr_revolver_cmts = list(i.resolver_commit_num for i in usriss_resolved)

    return Dataset.UserFeature(
        name=user,
        n_commits=len(usrcmts),
        n_issues=len(usriss),
        n_pulls=len(usrpulls),
        resolver_commits=usr_revolver_cmts,
    )


def get_background_data(owner: str, name: str, t: datetime):
    """Retrieve additional data for computing background related features"""
    all_issues: List[RepoIssue] = list(
        RepoIssue.objects(owner=owner, name=name, is_pull=False, created_at__lte=t)
    )
    all_commits: List[RepoCommit] = list(
        RepoCommit.objects(
            owner=owner,
            name=name,
            authored_at__lte=t,
            committed_at__lte=t,
        )
    )
    contributors, n_closed_issues, n_open_issues, issue_close_times = set(), 0, 0, []
    for i in all_issues:
        if i.state == "closed" and i.closed_at <= t:
            n_closed_issues += 1
            issue_close_times.append((i.closed_at - i.created_at).total_seconds())
        else:
            n_open_issues += 1
    for c in all_commits:
        contributors.update((c.author, c.committer))
    return contributors, n_closed_issues, n_open_issues, issue_close_times


def get_dynamics_data(owner: str, name: str, events: List[IssueEvent], t: datetime):
    """Retrieve additional data for computing dynamics related features"""
    labels, comments, comment_users, event_users = [], [], set(), set()
    for event in events:
        if event.time <= t:
            if event.actor is not None and event.actor != "ghost":
                event_users.add(event.actor)
            if event.type == "labeled":
                labels.append(event.label)
            elif event.type == "unlabeled":
                # Old GitHub issues do not have all labels in event list
                # In this case, we just ignore them
                if event.label in labels:
                    labels.remove(event.label)
            elif event.type == "commented":
                comments.append(event.comment)
                if event.actor is not None and event.actor != "ghost":
                    comment_users.add(event.actor)
    comment_users = [get_user_data(owner, name, user, t) for user in comment_users]
    event_users = [get_user_data(owner, name, user, t) for user in event_users]
    return labels, comments, comment_users, event_users


def get_dataset(issue: ResolvedIssue, before: datetime) -> Dataset:
    """For a resolved issue, get the corresponding data for RecGFI training."""
    query = Q(owner=issue.owner, name=issue.name, number=issue.number)

    existing = Dataset.objects(query & Q(before=before))
    if existing.count() > 0:
        logger.info(
            f"{issue.owner}/{issue.name}#{issue.number}-{before}: Already in dataset"
        )
        return existing.first()

    repo_issue: RepoIssue = RepoIssue.objects(query).first()
    if repo_issue.is_pull == True or repo_issue.state == "open":
        logger.error(f"{issue.owner}/{issue.name}#{issue.number}: Open or Pull Request")
        return

    logger.info(f"{issue.owner}/{issue.name}#{issue.number} (before {before}) start")

    repo: Repo = Repo.objects(owner=issue.owner, name=issue.name).first()
    contribs, n_closed, n_open, close_times = get_background_data(
        issue.owner, issue.name, before
    )
    prev_resolver_commits = [
        x.resolver_commit_num
        for x in ResolvedIssue.objects(
            name=issue.name, owner=issue.owner, resolved_at__lte=before
        )
    ]
    labels, comments, comment_users, event_users = get_dynamics_data(
        issue.owner, issue.name, issue.events, before
    )
    clean_body = delete_urls(delete_code_snippets(repo_issue.body))

    data = Dataset()

    data.owner = issue.owner
    data.name = issue.name
    data.number = issue.number
    data.created_at = repo_issue.created_at
    data.closed_at = repo_issue.closed_at
    data.before = before
    data.resolver_commit_num = issue.resolver_commit_num

    # ---------- Content ----------
    data.title = repo_issue.title
    data.body = clean_body
    data.len_title = count_text_len(repo_issue.title)
    data.len_body = count_text_len(clean_body)
    data.n_code_snips = count_code_snippets(repo_issue.body)
    data.n_urls = count_urls(repo_issue.body)
    data.n_imgs = count_imgs(repo_issue.body)
    data.coleman_liau_index = textstat.coleman_liau_index(clean_body)
    data.flesch_reading_ease = textstat.flesch_reading_ease(clean_body)
    data.flesch_kincaid_grade = textstat.flesch_kincaid_grade(clean_body)
    data.automated_readability_index = textstat.automated_readability_index(clean_body)
    data.labels = labels
    data.label_category = get_categorized_labels(labels)

    # ---------- Background ----------
    data.reporter_feat = get_user_data(issue.owner, issue.name, repo_issue.user, before)
    data.owner_feat = get_user_data(issue.owner, issue.name, issue.owner, before)
    data.prev_resolver_commits = prev_resolver_commits
    data.n_stars = sum(x.count for x in repo.monthly_stars if x.month <= before)
    data.n_pulls = sum(x.count for x in repo.monthly_pulls if x.month <= before)
    data.n_commits = sum(x.count for x in repo.monthly_commits if x.month <= before)
    data.n_contributors = len(contribs)
    data.n_closed_issues = n_closed
    data.n_open_issues = n_open
    data.r_open_issues = n_open / (n_open + n_closed) if n_open + n_closed > 0 else 0
    data.issue_close_time = np.median(close_times)

    # ---------- Dynamics ----------
    data.comments = comments
    data.events = [e.type for e in issue.events if e.time < before]
    data.comment_users = comment_users
    data.event_users = event_users

    data.save()
    logger.info(f"{issue.owner}/{issue.name}#{issue.number} (before {before}) is done")
    return data


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s (Process %(process)d) [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
        level=logging.INFO,
    )

    for resolved_issue in ResolvedIssue.objects():
        get_dataset(resolved_issue, resolved_issue.created_at)
        get_dataset(resolved_issue, resolved_issue.resolved_at)

    logger.info("Finish!")
