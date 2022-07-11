from typing import List, Optional, Any, Dict
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, BackgroundTasks, Header
from pydantic import BaseModel
from functools import cmp_to_key

from gfibot.collections import *
from ..models import GFIResponse, RepoQuery
from ..scheduled_tasks import update_repository_gfi_info

api = APIRouter()
logger = logging.getLogger(__name__)


def get_owner_and_name_form_github_request(repository: Dict):
    repo_full_name = repository["full_name"]
    repo_name = repository["name"]
    last_idx = repo_full_name.rfind("/")
    owner = repo_full_name[:last_idx]
    return owner, repo_name


def add_repo_from_github_app(user_collection, repositories):
    repo_info = []
    for repo in repositories:
        owner, repo_name = get_owner_and_name_form_github_request(repo)
        repo_info.append(
            {
                "name": repo_name,
                "owner": owner,
            }
        )

        queries = [[q.repo, q.owner] for q in user_collection.user_queries]
        if [repo_name, owner] not in queries:
            user_collection.update(
                push__user_queries={
                    "repo": repo_name,
                    "owner": owner,
                    "created_at": datetime.utcnow(),
                }
            )

        if len(GfiQueries.objects(Q(name=repo_name) & Q(owner=owner))) == 0:
            GfiQueries(
                name=repo_name,
                owner=owner,
                is_pending=True,
                is_finished=False,
                is_updating=False,
                is_github_app_repo=True,
                app_user_github_login=user_collection.github_login,
                _created_at=datetime.utcnow(),
                repo_config=GfiQueries.GfiRepoConfig(),
                update_config=GfiQueries.GfiUpdateConfig(
                    task_id=f"{owner}-{repo_name}-update",
                    interval=24 * 3600,
                ),
            ).save()
        else:
            logger.info(f"update new query {repo_name}/{owner}")
            GfiQueries.objects(Q(name=repo_name) & Q(owner=owner)).update(
                is_github_app_repo=True,
                app_user_github_login=user_collection.github_login,
                is_updating=False,
            )
            if (
                not GfiQueries.objects(Q(name=repo_name) & Q(owner=owner))
                .first()
                .update_config
            ):
                GfiQueries.objects(Q(name=repo_name) & Q(owner=owner)).update(
                    update_config=GfiQueries.GfiUpdateConfig(
                        task_id=f"{owner}-{repo_name}-update",
                        interval=24 * 3600,
                    )
                )
    user_token = user_collection.github_app_token
    if user_token:
        update_repos(repo_info)


def update_repos(repo_info):
    for repo in repo_info:
        name = repo["name"]
        owner = repo["owner"]
        task_id = f"{owner}-{name}-update"
        update_repository_gfi_info(task_id, owner=owner, repo=name)


def delete_repo_from_query(owner: str, name: str):
    """ Delete repo from GfiQueries """
    repo_query = GfiQueries.objects(Q(name=name) & Q(owner=owner)).first()
    if repo_query:
        repo_query.delete()


class GitHubAppResponse(BaseModel):
    sender: Dict[str, Any]
    action: str
    repositories: List[Dict[str, Any]]
    repositories_added: List[Dict[str, Any]]


@api.post('/actions/webhook', response_model=GFIResponse[str])
def github_app_webhook_process(x_github_event: str = Header(default=None)):
    """
    Process Github App webhook
    """
    event = request.headers.get("X-Github-Event")
    data = request.get_json()

    sender_id = data["sender"]["id"]
    user_collection = GfiUsers.objects(github_id=sender_id).first()

    if user_collection:
        if event == "installation":
            action = data["action"]
            if action == "created":
                repositories = data["repositories"]
                add_repo_from_github_app(user_collection, repositories)
            elif action == "deleted":
                repositories = data["repositories"]
                delete_repo_from_github_app(repositories)
            elif action == "suspend":
                repositories = data["repositories"]
                delete_repo_from_github_app(repositories)
            elif action == "unsuspend":
                add_repo_from_github_app(user_collection, repositories)
        elif event == "installation_repositories":
            action = data["action"]
            if action == "added":
                repositories = data["repositories_added"]
                add_repo_from_github_app(user_collection, repositories)
            elif action == "removed":
                repositories = data["repositories_removed"]
                delete_repo_from_github_app(repositories)
        elif event == "issues":
            action = data["action"]
        return {"code": 200, "result": "callback succeed for event {}".format(event)}
    else:
        return {"code": 404, "result": "user not found"}
