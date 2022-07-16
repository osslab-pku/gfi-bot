from typing import List
import math

from fastapi import APIRouter, HTTPException

from gfibot.collections import *
from gfibot.backend.models import GFIResponse, TrainingResult

api = APIRouter()
logger = logging.getLogger(__name__)


@api.get("/training/result", response_model=GFIResponse[List[TrainingResult]])
def get_training_result(name: Union[None, str] = None, owner: Union[None, str] = None):
    """
    get training result
    """
    if name != None and owner != None:
        query: TrainingSummary = (
            TrainingSummary.objects(Q(name=name, owner=owner))
            .only(*TrainingResult.__fields__)
            .order_by("-threshold")
            .first()
        )
        if not query:
            raise HTTPException(status_code=404, detail="Training result not found")
        else:
            q = {**query.to_mongo()}
            q["issues_train"] = len(q["issues_train"])
            q["issues_test"] = len(q["issues_test"])
            q = {
                k: 0.0 if isinstance(v, float) and math.isnan(v) else v
                for k, v in q.items()
            }  # convert nan to 0
            return GFIResponse(result=[TrainingResult(**q)])
    else:
        training_result: List[TrainingResult] = []
        for repo in Repo.objects():
            query: TrainingSummary = (
                TrainingSummary.objects(Q(name=repo.name, owner=repo.owner))
                .only(*TrainingResult.__fields__)
                .order_by("-threshold")
                .first()
            )
            if query:
                q = {**query.to_mongo()}
                q["issues_train"] = len(q["issues_train"])
                q["issues_test"] = len(q["issues_test"])
                q = {
                    k: 0.0 if isinstance(v, float) and math.isnan(v) else v
                    for k, v in q.items()
                }  # convert nan to 0
                training_result.append(TrainingResult(**q))
        # query_all = TrainingSummary.objects().only(*TrainingResult.__fields__).order_by("-threshold")
        # for query in query_all:
        #     q = {**query.to_mongo()}
        #     q["issues_train"] = len(q["issues_train"])
        #     q["issues_test"] = len(q["issues_test"])
        #     q = {k: 0. if isinstance(v, float) and math.isnan(v) else v for k, v in q.items()}  # convert nan to 0
        #     training_result.append(TrainingResult(**q))
        if not training_result:
            raise HTTPException(status_code=404, detail="Training result not found")
        return GFIResponse(result=training_result)
