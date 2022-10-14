from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

from gfibot.collections import *
from gfibot.backend.models import GFIResponse, GFIBrief
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
    repo: str, owner: str, start: Optional[int] = None, length: Optional[int] = None
):
    """
    Get brief info of issue
    """
    gfi_thres = get_repo_gfi_threshold(name=repo, owner=owner)
    newcomer_thres = get_repo_newcomer_threshold(name=repo, owner=owner)

    gfi_list: List[Prediction] = (
        Prediction.objects(
            Q(name=repo)
            & Q(owner=owner)
            # & Q(probability__gte=gfi_thres)
            & Q(threshold=newcomer_thres)
            & Q(state="open")
        )
        .only("name", "owner", "number", "threshold", "probability", "last_updated")
        .order_by(
            "-probability", "-number"
        )  # probability may be the same -> repeated issue
    )

    if start is not None and length is not None:
        gfi_list = gfi_list.skip(start).limit(length)

    if gfi_list:
        res_list: List[GFIBrief] = []
        for gfi in gfi_list:
            issue: RepoIssue = RepoIssue.objects(
                Q(name=repo) & Q(owner=owner) & Q(number=gfi.number)
            ).first()
            res_dict = (
                {**gfi.to_mongo(), **issue.to_mongo()} if issue else gfi.to_mongo()
            )
            res_list.append(GFIBrief(**res_dict))
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
            & Q(probability__gte=gfi_thres)
            & Q(threshold=newcomer_thres)
            & Q(state="open")
        ).count()
    )
