import pandas as pd
from fastapi.testclient import TestClient

from gfibot.backend.server import app
from gfibot.backend.models import GFIResponse, ModelEvaluationResponse
from gfibot.model.evaluation import run_systematic_evaluation


def test_run_systematic_evaluation(mock_mongodb):
    # Prepare dummy dataset dataframe
    df = pd.DataFrame(
        {
            "owner": ["owner"] * 10,
            "name": ["repo"] * 10,
            "number": list(range(10)),
            "is_gfi": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
            "created_at": pd.date_range("2023-01-01", periods=10),
            "closed_at": pd.date_range("2023-01-02", periods=10),
            "created_at_timestamp": list(range(10)),
            "len_title": [10, 12, 15, 8, 20, 11, 14, 9, 13, 16],
            "len_body": [100, 120, 150, 80, 200, 110, 140, 90, 130, 160],
            "n_code_snips": [1, 0, 2, 1, 0, 1, 2, 0, 1, 0],
            "n_urls": [1, 2, 0, 1, 3, 0, 1, 2, 1, 0],
            "bug_num": [1, 0, 0, 1, 0, 0, 1, 0, 0, 1],
        }
    )

    eval_doc = run_systematic_evaluation(df, owner="owner", name="repo", threshold=3)
    assert eval_doc is not None
    assert len(eval_doc.model_comparisons) > 0
    assert len(eval_doc.ablation_studies) > 0
    assert len(eval_doc.feature_importances) > 0

    client = TestClient(app)
    response = client.get("/api/model/evaluation?name=repo&owner=owner")
    assert response.status_code == 200
    res = GFIResponse[list[ModelEvaluationResponse]].parse_obj(response.json())
    assert len(res.result) == 1
    assert res.result[0].name == "repo"
    assert len(res.result[0].model_comparisons) > 0
