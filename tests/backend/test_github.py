import logging

from pydantic import HttpUrl
from fastapi.testclient import TestClient

from gfibot.collections import *
from gfibot.backend.server import app
from gfibot.backend.models import *


def test_github_redirect(mock_mongodb):
    client = TestClient(app)
    response = client.get("/api/github/app/installation",
        params={"code": "this_is_not_a_code"})
    logging.info(response.json())
    assert response.status_code == 500  # expect to fail


def test_get_github_oauth_url(mock_mongodb):
    client = TestClient(app)
    response = client.get("/api/github/login")
    logging.info(response.json())
    assert response.status_code == 200
    res = GFIResponse[HttpUrl].parse_obj(response.json())
    assert "github" in res.result


def test_github_webhook(mock_mongodb):
    client = TestClient(app)
    response = client.post("/api/github/actions/webhook",
        json={"action": "opened", "sender": {"id": 1}, "repository": {"full_name": "owner/name", "name": "name"},
            "issue": {"number": 1, "title": "title", "body": "body"}},
        headers={"X-GitHub-Event": "issues"})
    logging.info(response.json())
    assert response.status_code == 200
    res = GFIResponse[str].parse_obj(response.json())
    assert "not implemented" in res.result.lower()

    response = client.post("/api/github/actions/webhook",
        json={"action": "created", "sender": {"id": 1}, "repositories": [{"full_name": "owner/name", "name": "name"}]},
        headers={"X-GitHub-Event": "installation"})
    logging.info(response.json())
    assert response.status_code == 200

    response = client.post("/api/github/actions/webhook",
        json={"action": "deleted", "sender": {"id": 1}, "repositories": [{"full_name": "owner/name", "name": "name"}]},
        headers={"X-GitHub-Event": "installation"})
    logging.info(response.json())
    assert response.status_code == 200

    response = client.post("/api/github/actions/webhook",
        json={"action": "added", "sender": {"id": 1}, "repositories_added": [{"full_name": "owner/name", "name": "name"}]},
        headers={"X-GitHub-Event": "installation_repositories"})
    logging.info(response.json())
    assert response.status_code == 200

    response = client.post("/api/github/actions/webhook",
        json={"action": "removed", "sender": {"id": 1}, "repositories_removed": [{"full_name": "owner/name", "name": "name"}]},
        headers={"X-GitHub-Event": "installation_repositories"})
    logging.info(response.json())
    assert response.status_code == 200
