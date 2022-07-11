from typing import List
import math
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel


from gfibot.collections import *
from ..models import GFIResponse

api = APIRouter()
logger = logging.getLogger(__name__)

class TrainingResult(BaseModel):
    owner: str
    name: str
    issues_train: int
    issues_test: int
    n_resolved_issues: int
    n_newcomer_resolved: int
    accuracy: float
    auc: float
    last_updated: datetime


@api.get("/training/result", response_model=GFIResponse[List[TrainingResult]])
def get_training_result(name:Union[None, str]=None, owner: Union[None, str]=None):
    """
    get training result
    """
    if name != None and owner != None:
        query = TrainingSummary.objects(Q(name=name, owner=owner)).only(*TrainingResult.__fields__).order_by("-threshold").first()
        if not query:
            raise HTTPException(status_code=404, detail="Training result not found")
        else:
            q = {**query.to_mongo()}
            q["issues_train"] = len(q["issues_train"])
            q["issues_test"] = len(q["issues_test"])
            q = {k: 0. if isinstance(v, float) and math.isnan(v) else v for k, v in q.items()}  # convert nan to 0
            return GFIResponse(result=[TrainingResult(**q)])
    else:
        training_result: List[TrainingResult] = []
        for repo in Repo.objects():
            query = TrainingSummary.objects(Q(name=repo.name, owner=repo.owner)).only(*TrainingResult.__fields__).order_by("-threshold").first()
            if query:
                q = {**query.to_mongo()}
                q["issues_train"] = len(q["issues_train"])
                q["issues_test"] = len(q["issues_test"])
                q = {k: 0. if isinstance(v, float) and math.isnan(v) else v for k, v in q.items()}  # convert nan to 0
                training_result.append(TrainingResult(**q))
        if not training_result:
            raise HTTPException(status_code=404, detail="Training result not found")
        return GFIResponse(result=training_result)