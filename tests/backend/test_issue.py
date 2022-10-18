from gfibot.collections import *
from fastapi.testclient import TestClient
from gfibot.backend.server import app
from gfibot.backend.models import *


def test_get_number_of_issues(mock_mongodb):
    client = TestClient(app)
    response = client.get("/api/issue/num")
    logging.info(response.json())
    assert response.status_code == 200
    res = GFIResponse[int].parse_obj(response.json())
    assert res.result == OpenIssue.objects.count()


def test_get_repo_gfis(mock_mongodb):
    client = TestClient(app)
    response = client.get("/api/issue/gfi", params={"repo": "name", "owner": "owner"})
    logging.info(response.json())
    assert response.status_code == 200
    res = GFIResponse[List[GFIBrief]].parse_obj(response.json())
    assert res.result[0].name == "name"

    response = client.get(
        "/api/issue/gfi/num", params={"name": "name", "owner": "owner"}
    )
    logging.info(response.json())
    assert response.status_code == 200
    res2 = GFIResponse[int].parse_obj(response.json())
    assert res2.result == len(res.result)
