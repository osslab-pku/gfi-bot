import requests
import yagmail
import logging


from gfibot.collections import *
from gfibot.data.update import update_repo

logger = logging.getLogger(__name__)


def delete_repo(name, owner):
    repo_query = GfiQueries.objects(Q(name=name) & Q(owner=owner)).first()
    if repo_query:
        repo_query.delete()


def update_repos(token: str, repo_info):
    for repo in repo_info:
        name = repo["name"]
        owner = repo["owner"]
        is_updating = (
            GfiQueries.objects(Q(name=name) & Q(owner=owner)).first().is_updating
        )
        if not is_updating:
            logger.info(f"updating repo {repo['name']}")
            GfiQueries.objects(Q(name=name) & Q(owner=owner)).update(is_updating=True)
            update_repo(token, owner, name)


def add_comment_to_github_issue(
    user_github_id, repo_name, repo_owner, issue_number, comment
):
    """
    Add comment to GitHub issue
    """
    user_token = GfiUsers.objects(Q(github_id=user_github_id)).first().github_app_token
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
    user_github_id, repo_name, repo_owner, issue_number, label_name="good first issue"
):
    """
    Add label to Github issue
    """
    user_token = GfiUsers.objects(Q(github_id=user_github_id)).first().github_app_token
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
        summary = TrainingSummary.objects(Q(name=name) & Q(owner=owner))
        if len(summary):
            newcommer_summary = TrainingSummary.objects(
                Q(name=name) & Q(owner=owner) & Q(threshold=newcomer_threshold)
            )
            newcomer_issues = len(
                TrainingSummary.objects(
                    Q(name=name) & Q(owner=owner) & Q(threshold=newcomer_threshold)
                )
            )
            return newcomer_issues / len(summary)
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
