from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Union, Any
from datetime import datetime

from gfibot.collections import *
from ..models import GFIResponse


api = APIRouter()
logger = logging.getLogger(__name__)

@api.get("/num", response_model=GFIResponse[int])
def get_issue_num():
    """
    Get number of issues
    """
    return GFIResponse(result=OpenIssue.objects.count())


class IssueBrief(BaseModel):
    name: str
    owner: str
    number: int
    threshold: float
    probability: float
    last_updated: datetime


def get_repo_gfi_threshold(name: str, owner: str) -> float:
    repo = GfiQueries.objects(Q(name=name) & Q(owner=owner)).only('repo_config').first()
    if repo:
        return repo.repo_config.gfi_threshold
    return 0.5


@api.get("/gfi", response_model=GFIResponse[List[IssueBrief]])
def get_gfi_brief(name: str, owner: str):
    """
    Get brief info of issue
    """
    threshold = get_repo_gfi_threshold(name, owner)

    gfi_list = Prediction.objects(Q(name=name) & Q(owner=owner) & Q(probability__gte=threshold)).only(*IssueBrief.__fields__).order_by("-probability")

    if gfi_list:
        return GFIResponse(result=[IssueBrief(**gfi.to_mongo()) for gfi in gfi_list])
    raise HTTPException(status_code=404, detail="Good first issue not found")


@api.get("/gfi/num", response_model=GFIResponse[int])
def get_gfi_num(name: str, owner: str):
    """
    Get number of issues
    """
    threshold = get_repo_gfi_threshold(name, owner)

    return GFIResponse(result=Prediction.objects(Q(name=name) & Q(owner=owner) & Q(probability__gte=threshold)).count())