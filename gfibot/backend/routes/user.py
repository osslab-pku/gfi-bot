from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request

from gfibot.collections import *
from gfibot.backend.models import GFIResponse, RepoQuery, RepoSort, RepoConfig, UserSearchedRepo
from gfibot.backend.routes.github import redirect_from_github, get_oauth_app_login_url
from gfibot.backend.background_tasks import has_write_access, remove_repo_from_gfibot

api = APIRouter()
logger = logging.getLogger(__name__)


# may move these paths to github.py?
@api.get("/github/login")
def github_login():
    """
    Redirect to GitHub OAuth login page
    """
    return get_oauth_app_login_url()


@api.get("/github/callback")
def github_callback(code: str):
    """
    Redirect from GitHub OAuth callback page
    """
    return redirect_from_github(code, redirect_from="github_oauth_callback")


@api.get("/queries", response_model=GFIResponse[List[RepoQuery]])
def get_user_queries(user: str, filter: Optional[str] = None):
    user_record: GfiUsers = GfiUsers.objects(github_login=user).only('user_queries').first()
    if not user_record:
        raise HTTPException(status_code=404, detail="User not found")

    RANK_THRESHOLD = 3  # newcomer_thres used for ranking repos
    q = TrainingSummary.objects(threshold=RANK_THRESHOLD).filter(owner__ne="")  # "": global perf metrics
    repo_names = [repo.repo for repo in user_record.user_queries]
    repo_owners = [repo.owner for repo in user_record.user_queries]
    q = q.filter(name__in=repo_names, owner__in=repo_owners)

    if filter:
        if filter == RepoSort.GFIS:
            q = q.order_by("-n_gfis")
        elif filter == RepoSort.ISSUE_CLOSE_TIME:
            q = q.order_by("-issue_close_time")
        elif filter == RepoSort.NEWCOMER_RESOLVE_RATE:
            q = q.order_by("-r_newcomer_resolve")
        elif filter == RepoSort.STARS:
            q = q.order_by("-n_stars")
        else:
            raise HTTPException(status_code=400, detail="Invalid filter: expect one in {}".format(RepoSort.__members__))
    else:
        q = q.order_by("name")

    repos_list = list(q.only(*RepoQuery.__fields__))
    repo_queries = []
    for repo in repos_list:
        repo_q=GfiQueries.objects(name=repo.name, owner=repo.owner).only(*RepoQuery.__fields__).first()
        if repo_q:
            repo_queries.append(RepoQuery(**repo_q.to_mongo(), created_at=repo_q._created_at, finished_at=repo_q._finished_at))

    return GFIResponse(result=repo_queries)

    
# TODO:R RepoQuery not right
@api.delete("/queries", response_model=GFIResponse[List[RepoQuery]])
def delete_user_queries(request: Request):
    name = request.query_params.get("name")
    owner = request.query_params.get("owner")
    if not name or not owner:
        raise HTTPException(status_code=400, detail="Missing name or owner")
    user = request.query_params.get("user")
    if not user:
        raise HTTPException(status_code=400, detail="Missing user")

    user_q = GfiUsers.objects(github_login=user).only('user_queries').filter(user_queries__repo=name, user_queries__owner=owner)
    if not user_q or not user_q.user_queries:
        raise HTTPException(status_code=404, detail="User query not found")

    remove_repo_from_gfibot(name=name, owner=owner, user=user)

    return GFIResponse(result="Query deleted")


@api.get("/queries/config", response_model=GFIResponse[RepoConfig])
def get_user_queries_config(name: str, owner: str):
    repo_q = GfiQueries.objects(Q(name=name, owner=owner)).first()
    if not repo_q:
        raise HTTPException(status_code=404, detail="Repository not found")
    return GFIResponse(result=RepoConfig(**repo_q.repo_config))


@api.put("/queries/config")
def update_user_queries_config(repo_config: RepoConfig, request: Request):
    name = request.query_params.get("name")
    owner = request.query_params.get("owner")
    if not name or not owner:
        raise HTTPException(status_code=400, detail="Missing name or owner")
    user = request.query_params.get("user")
    if not user:
        raise HTTPException(status_code=400, detail="Missing user")
    if not has_write_access(owner, name, user):
        raise HTTPException(status_code=403, detail="You don't have write access to this repository")
    repo_q = GfiQueries.objects(Q(name=name, owner=owner)).first()
    if not repo_q:
        raise HTTPException(status_code=404, detail="Repository not found")
    repo_q.update(repo_config=dict(repo_config))
    return GFIResponse(result="Config updated")


@api.get("/searches", response_model=GFIResponse[List[UserSearchedRepo]])
def get_user_searches(user: str):
    user_record = GfiUsers.objects(github_login=user).only("user_searches").first()
    if not user_record:
        raise HTTPException(status_code=404, detail="User not found")
    searched_repos = [UserSearchedRepo(**repo.to_mongo(), name=repo.repo) for repo in user_record.user_searches]
    return GFIResponse(result=searched_repos)


@api.delete("/searches", response_model=GFIResponse[List[UserSearchedRepo]])
def delete_user_searches(request: Request):
    user = request.query_params.get("user", None)
    sid = request.query_params.get("id", None)
    if not user:
        raise HTTPException(status_code=400, detail="user not specified")
    if sid and not sid.isdigit():
        raise HTTPException(status_code=400, detail="id must be an integer")
    user_record: GfiUsers = GfiUsers.objects(github_login=user).only("user_searches").first()
    if not user_record:
        raise HTTPException(status_code=404, detail="User not found")
    if sid is not None:
        # delete where increment == id
        # seems to be a bug in mongoengine: https://stackoverflow.com/questions/32301142
        GfiUsers.objects(github_login=user).update_one(
            __raw__={
                "$pull": {
                    "user_searches": {
                        "increment": int(sid)
                    }
                }
            }
        )
    else:
        # delete all user searches
        GfiUsers.objects(github_login=user).update_one(
            __raw__={
                "$set": {
                    "user_searches": []
                }
            }
        )
    searched_repos = [UserSearchedRepo(**repo.to_mongo(), name=repo.repo) for repo in user_record.user_searches]
    return GFIResponse(result=searched_repos)