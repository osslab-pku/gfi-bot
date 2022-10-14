from typing import List, Optional, Any, Dict
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
import requests

from gfibot import CONFIG
from gfibot.collections import *
from gfibot.backend.models import (
    GFIResponse,
    RepoQuery,
    RepoBrief,
    RepoDetail,
    RepoSort,
    Config,
)
from gfibot.backend.background_tasks import (
    add_repo_to_gfibot,
    has_write_access,
    schedule_repo_update_now,
)
from gfibot.backend.routes.issue import (
    get_repo_gfi_threshold,
    get_repo_newcomer_threshold,
)

api = APIRouter()
logger = logging.getLogger(__name__)


@api.get("/num", response_model=GFIResponse[int])
def get_repo_num(language: Optional[str] = None):
    """
    Get number of repositories
    """
    if language:
        return GFIResponse(result=Repo.objects.filter(language=language).count())
    return GFIResponse(result=Repo.objects.count())


@api.get("/info", response_model=GFIResponse[RepoBrief])
def get_repo_brief(name: str, owner: str):
    """
    Get brief info of repository
    """
    repo = (
        Repo.objects(Q(name=name) & Q(owner=owner)).only(*RepoBrief.__fields__).first()
    )
    if repo:
        return GFIResponse(result=RepoBrief(**repo.to_mongo()))
    raise HTTPException(status_code=404, detail="Repository not found")


@api.get("/info/detail", response_model=GFIResponse[RepoDetail])
def get_repo_detail(name: str, owner: str):
    """
    Get detail info of repository
    """
    repo = (
        Repo.objects(Q(name=name) & Q(owner=owner)).only(*RepoDetail.__fields__).first()
    )
    if repo:
        return GFIResponse(result=RepoDetail(**repo.to_mongo()))
    raise HTTPException(status_code=404, detail="Repository not found")


@api.get("/info/", response_model=GFIResponse[List[RepoDetail]])
def get_paged_repo_detail(
    start: int,
    length: int,
    lang: Optional[str] = None,
    filter: Optional[RepoSort] = None,
):
    """
    Get detailed info of repository (paged)
    """
    RANK_THRESHOLD = get_repo_newcomer_threshold(
        "", ""
    )  # newcomer_thres used for ranking repos

    q = TrainingSummary.objects(threshold=RANK_THRESHOLD).filter(
        owner__ne=""
    )  # "": global perf metrics

    if lang:
        # TODO: add language field to TrainingSummary (current code might be slow)
        lang_repos = list(Repo.objects().filter(language=lang).only("name", "owner"))
        lang_names = [repo.name for repo in lang_repos]
        lang_owners = [repo.owner for repo in lang_repos]
        q = q.filter(name__in=lang_names, owner__in=lang_owners)

    if filter:
        if filter == RepoSort.GFIS:
            q = q.order_by("-n_gfis")
        elif filter == RepoSort.ISSUE_CLOSE_TIME:
            q = q.order_by("issue_close_time")
        elif filter == RepoSort.NEWCOMER_RESOLVE_RATE:
            q = q.order_by("-r_newcomer_resolve")
        elif filter == RepoSort.STARS:
            q = q.order_by("-n_stars")
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid filter: expect one in {}".format(RepoSort.__members__),
            )
    else:
        q = q.order_by("name")

    repos_list = list(q.skip(start).limit(length).only(*RepoQuery.__fields__))
    repos_detail = []

    for repo in repos_list:
        repo_detail = (
            Repo.objects(Q(name=repo.name) & Q(owner=repo.owner))
            .only(*RepoDetail.__fields__)
            .first()
        )
        if not repo_detail:
            logger.error(
                "Repo {}/{} is present in TrainingSummary but not in Repo".format(
                    repo.name, repo.owner
                )
            )
        else:
            repos_detail.append(RepoDetail(**repo_detail.to_mongo()))

    return GFIResponse(result=repos_detail)

    # # fetch repo stats on-demand would be more elegant
    # repos_brief = []
    # for repo in repos_list:
    #     repo_brief = Repo.objects(Q(name=repo.name) & Q(owner=repo.owner)).only(*RepoBrief.__fields__).first()
    #     if not repo_brief:
    #         logger.error("Repo {}/{} is present in TrainingSummary but not in Repo".format(repo.name, repo.owner))
    #     else:
    #         repos_brief.append(RepoBrief(**repo_brief.to_mongo()))
    # return GFIResponse(result=repos_brief)


@api.get("/info/paged", response_model=GFIResponse[List[RepoBrief]])
def get_paged_repo_brief(
    start: int,
    length: int,
    lang: Optional[str] = None,
    filter: Optional[RepoSort] = None,
):
    """
    Get brief info of repository (paged)
    """
    RANK_THRESHOLD = get_repo_newcomer_threshold(
        "", ""
    )  # newcomer_thres used for ranking repos

    q = TrainingSummary.objects(threshold=RANK_THRESHOLD).filter(
        owner__ne=""
    )  # "": global perf metrics

    if lang:
        # TODO: add language field to TrainingSummary (current code might be slow)
        lang_repos = list(Repo.objects().filter(language=lang).only("name", "owner"))
        lang_names = [repo.name for repo in lang_repos]
        lang_owners = [repo.owner for repo in lang_repos]
        q = q.filter(name__in=lang_names, owner__in=lang_owners)

    if filter:
        if filter == RepoSort.GFIS:
            q = q.order_by("-n_gfis")
        elif filter == RepoSort.ISSUE_CLOSE_TIME:
            q = q.order_by("issue_close_time")
        elif filter == RepoSort.NEWCOMER_RESOLVE_RATE:
            q = q.order_by("-r_newcomer_resolve")
        elif filter == RepoSort.STARS:
            q = q.order_by("-n_stars")
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid filter: expect one in {}".format(RepoSort.__members__),
            )
    else:
        q = q.order_by("name")

    repos_list = list(q.skip(start).limit(length).only(*RepoQuery.__fields__))
    repos_brief = []

    for repo in repos_list:
        repo_detail = (
            Repo.objects(Q(name=repo.name) & Q(owner=repo.owner))
            .only(*RepoBrief.__fields__)
            .first()
        )
        if not repo_detail:
            logger.error(
                "Repo {}/{} is present in TrainingSummary but not in Repo".format(
                    repo.name, repo.owner
                )
            )
        else:
            repos_brief.append(RepoBrief(**repo_detail.to_mongo()))

    return GFIResponse(result=repos_brief)


@api.get("/info/search", response_model=GFIResponse[List[RepoDetail]])
def search_repo_detail(
    user: Optional[str] = None, repo: Optional[str] = None, url: Optional[str] = None
):
    """
    Search repository by owner, name, url or description
    url: GitHub repo url http(s)://github.com/<owner>/<repo>
    repo: query string (owner,name,descrption)
    """
    owner = ""
    if url:
        # parse url
        url_parts = urlparse(url)
        if url_parts.netloc == "github.com":
            try:
                owner, repo = url_parts.path.split("/")[1:]
            except IndexError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid url: expect http(s)://github.com/<owner>/<repo>",
                )
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid url: expect http(s)://github.com/<owner>/<repo>",
            )
    if not repo:
        raise HTTPException(status_code=400, detail="Must specify repo or url")

    # text search
    query_str = repo if not owner else owner + " " + repo
    repos_q = (
        Repo.objects.search_text(query_str)
        .only(*RepoDetail.__fields__)
        .order_by("$text_score")
        .limit(10)
    )
    # if repos_q.count() == 0:
    #     raise HTTPException(status_code=404, detail="Repository not found")
    repos_search = [RepoDetail(**repo.to_mongo()) for repo in repos_q]

    if user:  # append to user search history
        gfiuser = GfiUsers.objects(github_login=user).first()
        if gfiuser:
            for repo in repos_search:
                gfiuser.update(
                    push__user_searches={
                        "repo": repo.name,
                        "owner": repo.owner,
                        "created_at": datetime.utcnow(),
                        "increment": len(gfiuser.user_searches) + 1,
                    }
                )

    return GFIResponse(result=repos_search)


@api.get("/language", response_model=GFIResponse[List[str]])
def get_repo_language():
    """
    Get all languages
    """
    return GFIResponse(
        result=list(Repo.objects.filter(language__ne=None).distinct("language"))
    )


class RepoAddModel(BaseModel):
    user: str
    repo: str
    owner: str


@api.post("/add", response_model=GFIResponse[str])
def add_repo(data: RepoAddModel):
    """
    Add repository to GFI-Bot
    """
    user, repo, owner = data.user, data.repo, data.owner
    gfi_user = GfiUsers.objects(Q(github_login=user)).first()
    if not gfi_user:
        raise HTTPException(status_code=400, detail="User not registered")
    if not gfi_user.github_access_token:
        raise HTTPException(status_code=400, detail="GitHub user token not found")

    query = GfiQueries.objects.filter(Q(name=repo, owner=owner)).first()
    if not query:
        add_repo_to_gfibot(owner=owner, name=repo, user=user)
        return GFIResponse(result="Repository added")
    if query.is_pending:
        return GFIResponse(result="Repository is being processed by GFI-Bot")
    else:
        return GFIResponse(result="Repository already exists")


@api.get("/update/config", response_model=GFIResponse[Config])
def get_repo_update_config(name: str, owner: str):
    """
    Get repo config
    """
    repo_q = GfiQueries.objects(Q(name=name, owner=owner)).first()
    if not repo_q:
        raise HTTPException(status_code=404, detail="Repository not registered")
    return GFIResponse(
        result=Config(
            update_config=repo_q.update_config.to_mongo(),
            repo_config=repo_q.repo_config.to_mongo(),
        )
    )


class UpdateModel(BaseModel):
    name: str
    owner: str
    github_login: str


@api.put("/update/", response_model=GFIResponse[str])
def force_repo_update(data: UpdateModel):
    """
    Force update a repository (next update will be scheduled 24h later)
    """
    owner, name, github_login = data.owner, data.name, data.github_login
    if not has_write_access(owner=owner, name=name, user=github_login):
        raise HTTPException(
            status_code=403, detail="You don't have write access to this repository"
        )
    repo_q = GfiQueries.objects(Q(name=name) & Q(owner=owner)).first()
    if not repo_q:
        raise HTTPException(status_code=404, detail="Repository not found")
    update_config = repo_q.update_config
    if update_config != None:
        task_id = update_config.task_id
        # interval = update_config.interval
    else:
        # create update config for manually updated projects
        task_id = f"{owner}-{name}-update"
        # interval = 24 * 3600  # update daily by default
        # repo_q.update(
        #     update_config={
        #         "task_id": task_id,
        #         "interval": interval,
        #     }
        # )

    # alter update schedule
    user_q: GfiUsers = GfiUsers.objects(github_login=github_login).first()
    if user_q:
        token = (
            user_q.github_access_token
            if user_q.github_access_token
            else user_q.github_app_token
        )
        schedule_repo_update_now(name=name, owner=owner, token=token)
    else:
        raise HTTPException(status_code=400, detail="User not registered")

    return GFIResponse(result="Repository update scheduled")


@api.get("/badge", response_class=Response)
def get_badge(name: str, owner: str):
    """
    Get README badge for a repository
    """
    prob_thres = get_repo_gfi_threshold(name, owner)
    newcomer_thres = get_repo_newcomer_threshold(name, owner)
    n_gfis = Prediction.objects(
        Q(name=name)
        & Q(owner=owner)
        & Q(probability__gte=prob_thres)
        & Q(threshold=newcomer_thres)
    ).count()
    img_src = "https://img.shields.io/badge/{}-{}".format(
        f"recommended good first issues - {n_gfis}", "success"
    )
    svg = requests.get(img_src).content
    return Response(svg, media_type="image/svg+xml")


@api.get("/badge/{owner}/{name}", response_class=Response)
def get_badge_by_path(name: str, owner: str):
    return get_badge(name, owner)
