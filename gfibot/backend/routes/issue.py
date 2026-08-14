from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

from gfibot.collections import *
from gfibot.backend.models import GFIResponse, GFIBrief, IssueSort
from gfibot import CONFIG


api = APIRouter()
logger = logging.getLogger(__name__)


@api.get("/num", response_model=GFIResponse[int])
def get_issue_num():
    """
    Get number of open issues
    """
    return GFIResponse(result=OpenIssue.objects.count())


def get_repo_gfi_threshold(name: str, owner: str) -> float:
    repo: GfiQueries = (
        GfiQueries.objects(Q(name=name) & Q(owner=owner)).only("repo_config").first()
    )
    if repo:
        return repo.repo_config.gfi_threshold
    try:
        return CONFIG["gfibot"]["default_gfi_threshold"]
    except KeyError:
        return 0.5


def get_repo_newcomer_threshold(name: str, owner: str) -> float:
    repo: GfiQueries = (
        GfiQueries.objects(Q(name=name) & Q(owner=owner)).only("repo_config").first()
    )
    if repo:
        return repo.repo_config.newcomer_threshold
    try:
        return CONFIG["gfibot"]["default_newcomer_threshold"]
    except KeyError:
        return 5


@api.get("/gfi", response_model=GFIResponse[List[GFIBrief]])
def get_gfi_brief(
    repo: str,
    owner: str,
    start: Optional[int] = None,
    length: Optional[int] = None,
    sort: Optional[IssueSort] = None,
):
    """
    Get brief info of issue with rich metadata and sorting options
    """
    gfi_thres = get_repo_gfi_threshold(name=repo, owner=owner)
    newcomer_thres = get_repo_newcomer_threshold(name=repo, owner=owner)

    gfi_query = Prediction.objects(
        Q(name=repo)
        & Q(owner=owner)
        & Q(threshold=newcomer_thres)
        & Q(state="open")
    )

    if sort == IssueSort.PROBABILITY_ASC:
        gfi_query = gfi_query.order_by("probability", "number")
    elif sort == IssueSort.NEWEST:
        gfi_query = gfi_query.order_by("-last_updated", "-number")
    elif sort == IssueSort.OLDEST:
        gfi_query = gfi_query.order_by("last_updated", "number")
    else:  # default PROBABILITY_DESC
        gfi_query = gfi_query.order_by("-probability", "-number")

    if start is not None and length is not None:
        gfi_list = list(gfi_query.skip(start).limit(length))
    else:
        gfi_list = list(gfi_query)

    if gfi_list:
        res_list: List[GFIBrief] = []
        for gfi in gfi_list:
            issue: Optional[RepoIssue] = RepoIssue.objects(
                Q(name=repo) & Q(owner=owner) & Q(number=gfi.number)
            ).first()

            gfi_dict = gfi.to_mongo().to_dict()
            gfi_dict.pop("_id", None)

            if issue:
                issue_dict = issue.to_mongo().to_dict()
                issue_dict.pop("_id", None)
                body_raw = issue_dict.get("body", "") or ""
                # Cap body description snippet at 300 chars (#33)
                capped_body = body_raw[:300] + "..." if len(body_raw) > 300 else body_raw
                issue_dict["body"] = capped_body
                gfi_dict.update(issue_dict)

            # Rich metadata (#32, #33)
            gfi_dict["html_url"] = f"https://github.com/{owner}/{repo}/issues/{gfi.number}"
            gfi_dict["gfi_probability_percentage"] = f"{gfi.probability * 100:.2f}%"

            res_list.append(GFIBrief(**gfi_dict))
        return GFIResponse(result=res_list)
    raise HTTPException(status_code=404, detail="Good first issue not found")



@api.get("/gfi/num", response_model=GFIResponse[int])
def get_gfi_num(
    name: Optional[str] = None,
    owner: Optional[str] = None,
):
    """
    Get number of issues
    """
    newcomer_thres = get_repo_newcomer_threshold(name=name, owner=owner)
    gfi_thres = get_repo_gfi_threshold(name=name, owner=owner)
    if name is None or owner is None:
        return GFIResponse(
            result=Prediction.objects(
                Q(probability__gte=0.5, threshold=newcomer_thres, state="open")
            ).count()
        )

    gfi_thres = get_repo_gfi_threshold(name, owner)
    return GFIResponse(
        result=Prediction.objects(
            Q(name=name)
            & Q(owner=owner)
            # & Q(probability__gte=gfi_thres)
            & Q(threshold=newcomer_thres)
            & Q(state="open")
        ).count()
    )
