from lib2to3.pgen2.pgen import generate_grammar
import requests
import yagmail
import logging
import json

from gfibot.collections import *

logger = logging.getLogger(__name__)


def generate_repo_update_task_id(owner, name):
    return f"{owner}-{name}-update"


def get_repo_info_detailed(repo: Repo):
    def get_month_count(mounth_counts):
        return [
            {
                "month": item.month,
                "count": item.count,
            }
            for item in mounth_counts
        ]

    return {
        "name": repo.name,
        "owner": repo.owner,
        "description": repo.description,
        "language": repo.language,
        "topics": repo.topics,
        "monthly_stars": get_month_count(repo.monthly_stars),
        "monthly_commits": get_month_count(repo.monthly_commits),
        "monthly_issues": get_month_count(repo.monthly_issues),
        "monthly_pulls": get_month_count(repo.monthly_pulls),
    }


def delete_repo_from_query(name, owner):
    repo_query = GfiQueries.objects(Q(name=name) & Q(owner=owner)).first()
    if repo_query:
        repo_query.delete()


def add_comment_to_github_issue(
    github_login, repo_name, repo_owner, issue_number, comment
):
    """
    Add comment to GitHub issue
    """
    user_token = GfiUsers.objects(Q(github_login=github_login)).first().github_app_token
    if user_token:
        headers = {
            "Authorization": "token {}".format(user_token),
            "Content-Type": "application/json",
        }
        url = "https://api.github.com/repos/{}/{}/issues/{}/comments".format(
            repo_owner, repo_name, issue_number
        )
        r = requests.post(url, headers=headers, data=json.dumps({"body": comment}))
        return r.status_code
    else:
        return 403


def add_gfi_label_to_github_issue(
    github_login, repo_name, repo_owner, issue_number, label_name="good first issue"
):
    """
    Add label to Github issue
    """
    user_token = GfiUsers.objects(Q(github_login=github_login)).first().github_app_token
    if user_token:
        headers = {"Authorization": "token {}".format(user_token)}
        url = "https://api.github.com/repos/{}/{}/issues/{}/labels".format(
            repo_owner, repo_name, issue_number
        )
        r = requests.post(url, headers=headers, json=["{}".format(label_name)])
        return r.status_code
    else:
        return 403


def get_repo_stars(owner, name):
    """
    Get number of stars for a repo
    """
    repo = Repo.objects(Q(name=name) & Q(owner=owner)).first()
    if repo:
        stars = 0
        for monthly_star in repo.monthly_stars:
            stars += monthly_star.count
        return stars
    return 0


def get_repo_gfi_num(owner, name):
    """
    Get number of GFIs for a repo
    """
    repo = Repo.objects(Q(name=name) & Q(owner=owner)).first()
    repo_query = GfiQueries.objects(Q(name=name) & Q(owner=owner)).first()
    if repo:
        gfi_threshold = 0.5
        if repo_query and repo_query.repo_config:
            gfi_threshold = repo_query.repo_config.gfi_threshold
        gfi_list = Prediction.objects(
            Q(name=name) & Q(owner=owner) & Q(probability__gte=gfi_threshold)
        )
        if gfi_list:
            return len(gfi_list)
    return 0


def get_newcomer_resolved_issue_rate(owner, name):
    repo = Repo.objects(Q(name=name) & Q(owner=owner)).first()
    repo_query = GfiQueries.objects(Q(name=name) & Q(owner=owner)).first()
    if repo:
        newcomer_threshold = 5
        if repo_query and repo_query.repo_config:
            newcomer_threshold = repo_query.repo_config.newcomer_threshold
        summary = TrainingSummary.objects(
            Q(name=name) & Q(owner=owner) & Q(threshold=newcomer_threshold)
        ).first()
        if summary:
            all_issues = summary.n_resolved_issues
            new_comer_resolved = summary.n_newcomer_resolved
            if all_issues > 0:
                return new_comer_resolved / all_issues
    return 0


def send_email(user_github_login, subject, body):
    """
    Send email to user
    """

    logger.info("send email to user {}".format(user_github_login))

    user_email = GfiUsers.objects(github_login=user_github_login).first().github_email

    email = GfiEmail.objects().first().email
    password = GfiEmail.objects().first().password

    logger.info("Sending email to {} using {}".format(user_email, email))

    if user_email != None:
        yag = yagmail.SMTP(email, password)
        yag.send(user_email, subject, body)
        yag.close()
