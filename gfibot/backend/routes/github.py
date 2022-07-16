from typing import List, Optional, Any, Dict, Final
from urllib.parse import urlencode, parse_qsl
import json

from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import RedirectResponse
from numpy import full
from pydantic import BaseModel, HttpUrl
import requests

from gfibot.collections import *
from gfibot.backend.models import GFIResponse, RepoQuery, GitHubRepo, GitHubAppWebhookResponse, GitHubUserInfo
from gfibot.backend.background_tasks import add_repo_to_gfibot, remove_repo_from_gfibot

api = APIRouter()
logger = logging.getLogger(__name__)


def add_repos_from_github_app(user_collection: GfiUsers, repositories: List[GitHubRepo]) -> int:
    """
    Add repositories update jobs to background tasks (returns immediately)
    returns: number of added jobs
    """
    repos_failed = []
    user = user_collection.github_login
    for repo in repositories:
        owner, name = repo.full_name.split("/")
        try:
            add_repo_to_gfibot(owner=owner, name=name, user=user)
        except Exception as e:
            repos_failed.append(repo.full_name)
            logger.warning(f"failed to add repo {owner}/{name} to gfibot: {e}")
    if repos_failed:
        raise HTTPException(500, f"failed to add {len(repos_failed)}/{len(repositories)} repos to gfibot: {repos_failed}")
    return len(repositories)


def delete_repos_from_github_app(user_collection: GfiUsers, repositories: List[GitHubRepo]) -> int:
    """
    Delete repositories from background tasks (returns immediately)
    returns: number of deleted jobs
    """
    repos_failed = []
    user = user_collection.github_login
    for repo in repositories:
        owner, name = repo.full_name.split("/")
        try:
            remove_repo_from_gfibot(owner=owner, name=name, user=user)
        except Exception as e:
            repos_failed.append(repo.full_name)
            logger.warning(f"failed to delete repo {owner}/{name} from gfibot: {e}")
    if repos_failed:
        raise HTTPException(500, f"failed to delete {len(repos_failed)}/{len(repositories)} repos from gfibot: {repos_failed}")
    return len(repositories)


@api.post('/actions/webhook', response_model=GFIResponse[str])
def github_app_webhook_process(data: GitHubAppWebhookResponse, x_github_event: str = Header(default=None)) -> GFIResponse[str]:
    """
    Process Github App webhook
    """
    event = x_github_event
    sender_id = data.sender["id"]
    user_collection: GfiUsers = GfiUsers.objects(github_id=sender_id).first()
    if not user_collection:
        logger.error(f"user with github id {sender_id} not found")
        raise HTTPException(status_code=404, detail="user not found")

    processed_repos = 0
    if event == "installation":
        expected_repos = len(data.repositories)
        action = data.action
        if action == "created":
            processed_repos = add_repos_from_github_app(user_collection, data.repositories)
        elif action == "deleted":
            processed_repos = delete_repos_from_github_app(user_collection, data.repositories)
        elif action == "suspend":
            processed_repos = delete_repos_from_github_app(user_collection, data.repositories)
        elif action == "unsuspend":
            processed_repos = add_repos_from_github_app(user_collection, data.repositories)
    elif event == "installation_repositories":
        action = data.action
        if action == "added":
            expected_repos = len(data.repositories_added)
            processed_repos = add_repos_from_github_app(user_collection, data.repositories_added)
        elif action == "removed":
            expected_repos = len(data.repositories_removed)
            processed_repos = delete_repos_from_github_app(user_collection, data.repositories_removed)
    elif event == "issues":
        action = data.action
        logger.info(f"{action} issue {data.issue['number']} in {data.repository.full_name}")
        return GFIResponse(result="Not implemented: event=%s" % event)
    else:
        return GFIResponse(result="Not implemented: event=%s" % event)

    if processed_repos != expected_repos:
        raise HTTPException(status_code=500, detail=f"{processed_repos} repos processed, {expected_repos} repos in total")
    return GFIResponse(result=f"{processed_repos} repos processed")


GITHUB_LOGIN_URL: Final = "https://github.com/login/oauth/authorize"
GITHUB_OAUTH_URL: Final = "https://github.com/login/oauth/access_token"
GITHUB_USER_API_URL: Final = "https://api.github.com/user"

@api.get('/login', response_model=GFIResponse[HttpUrl])
def get_oauth_app_login_url():
    """
    Get oauth url of the github app
    """
    oauth_record: GithubTokens = GithubTokens.objects().first()
    if not oauth_record:
        raise HTTPException(status_code=404, detail="oauth record not found in database")
    oauth_client_id = GithubTokens.objects().first().client_id
    return GFIResponse(result=f"{GITHUB_LOGIN_URL}?client_id={oauth_client_id}")


@api.get('/app/installation', response_class=RedirectResponse)
def redirect_from_github(code: str, redirect_from: str="github_app_login"):
    """
    Redirect from github webapp
    """
    oauth_record: GithubTokens = GithubTokens.objects().first()
    if not oauth_record:
        raise HTTPException(status_code=500, detail="oauth record not found in database")

    # auth github app
    r = requests.post(
            GITHUB_OAUTH_URL,
            data={
                "client_id": oauth_record.client_id,
                "client_secret": oauth_record.client_secret,
                "code": code,
            },
        )
    if r.status_code != 200 or not "access_token" in r.text:
        logger.error(f"error getting access token via oauth: code={code} response={r.text}")
        raise HTTPException(status_code=500, detail="Failed to obtain access token via oauth")
    access_token = dict(parse_qsl(r.text))["access_token"]

    # get user info
    r = requests.get(GITHUB_USER_API_URL, headers={"Authorization": f"token {access_token}"})
    if r.status_code != 200:
        logger.error(f"error getting user info via oauth: code={code} response={r.text}")
        raise HTTPException(status_code=500, detail="Failed to obtain user info via oauth")
    user_res = GitHubUserInfo(**json.loads(r.text))
    
    update_obj = {f"github_{k}": v for k, v in dict(user_res).items() if k not in ["twitter_username"]}
    update_obj["twitter_user_name"] = user_res.twitter_username
    
    if redirect_from == "github_app_login":
        update_obj["github_app_token"] = access_token
    else:
        update_obj["github_access_token"] = access_token

    GfiUsers.objects(github_id=user_res.id).upsert_one(**update_obj)

    logger.info(f"user {user_res.login} logged in via {redirect_from}")

    params = {
        "github_login": user_res.login,
        "github_name": user_res.name,
        "github_id": user_res.id,
        "github_token": access_token,
        "github_avatar_url": user_res.avatar_url,
    }

    return RedirectResponse(url="/login/redirect?" + urlencode(params))