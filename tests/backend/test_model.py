from gfibot.collections import *
from fastapi.testclient import TestClient
from gfibot.backend.server import app
from gfibot.backend.models import *


def test_get_training_result(mock_mongodb):
    client = TestClient(app)
    response = client.get("/api/model/training/result")
    assert response.status_code == 200
    res = GFIResponse[List[TrainingResult]].parse_obj(response.json())
    assert len(res.result) == 2
