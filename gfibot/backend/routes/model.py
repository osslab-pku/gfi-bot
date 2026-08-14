from typing import List, Optional
import math

from fastapi import APIRouter

from gfibot.collections import *
from gfibot.backend.models import GFIResponse, TrainingResult, ModelEvaluationResponse
from .issue import get_repo_newcomer_threshold

api = APIRouter()
logger = logging.getLogger(__name__)


@api.get("/training/result", response_model=GFIResponse[List[TrainingResult]])
def get_training_result(
    name: Union[None, str] = None,
    owner: Union[None, str] = None,
):
    """
    get training result
    """
    newcomer_thres = get_repo_newcomer_threshold(name=name, owner=owner)

    if name != None and owner != None:
        query: TrainingSummary = (
            TrainingSummary.objects(
                Q(name=name, owner=owner) & Q(threshold=newcomer_thres)
            )
            .only(*TrainingResult.__fields__)
            .first()
        )
        if not query:
            return GFIResponse(result=[])
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
            newcomer_thres = get_repo_newcomer_threshold(
                name=repo.name, owner=repo.owner
            )
            query: TrainingSummary = (
                TrainingSummary.objects(
                    Q(name=repo.name, owner=repo.owner) & Q(threshold=newcomer_thres)
                )
                .only(*TrainingResult.__fields__)
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
        return GFIResponse(result=training_result)


@api.get("/evaluation", response_model=GFIResponse[List[ModelEvaluationResponse]])
def get_model_evaluations(
    name: Optional[str] = None,
    owner: Optional[str] = None,
):
    """
    Get systematic ML model evaluation results (model comparison, ablation study, feature importance).
    """
    newcomer_thres = get_repo_newcomer_threshold(name=name or "", owner=owner or "")

    if name is not None and owner is not None:
        eval_docs = ModelEvaluation.objects(Q(name=name, owner=owner) & Q(threshold=newcomer_thres))
    else:
        eval_docs = ModelEvaluation.objects()

    results: List[ModelEvaluationResponse] = []
    for doc in eval_docs:
        mongo_dict = doc.to_mongo().to_dict()
        mongo_dict.pop("_id", None)
        results.append(ModelEvaluationResponse(**mongo_dict))

    return GFIResponse(result=results)

