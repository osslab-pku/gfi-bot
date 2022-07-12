from datetime import datetime, timezone
from bson.json_util import DEFAULT_JSON_OPTIONS
from gfibot.collections import *

from fastapi.testclient import TestClient
from gfibot.backend.server import app
from gfibot.backend.models import *


def test_get_number_of_repos():
    client = TestClient(app)
    response = client.get("/repos/num")
    assert response.status_code == 200
    res = GFIResponse[int].parse_obj(response.json())
    assert res.result == Repo.objects.count()


def test_get_repo_brief():
    client = TestClient(app)
    response = client.get("/repos/info/gfibot/gfibot")
    assert response.status_code == 200
    res = GFIResponse[RepoBrief].parse_obj(response.json())
    assert res.result.name == "name"
    assert res.result.owner == "owner"