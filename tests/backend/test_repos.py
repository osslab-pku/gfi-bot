from gfibot.collections import *
from fastapi.testclient import TestClient
from gfibot.backend.server import app
from gfibot.backend.models import *


def test_get_number_of_repos(mock_mongodb):
    client = TestClient(app)
    response = client.get("/api/repos/num")
    assert response.status_code == 200
    res = GFIResponse[int].parse_obj(response.json())
    assert res.result == Repo.objects.count()

    # num by language
    response = client.get("/api/repos/num?language=Python")
    assert response.status_code == 200
    res = GFIResponse[int].parse_obj(response.json())
    assert res.result == Repo.objects(language="Python").count()


def test_get_repo_brief(mock_mongodb):
    client = TestClient(app)
    response = client.get("/api/repos/info?name=name&owner=owner")
    assert response.status_code == 200
    res = GFIResponse[RepoBrief].parse_obj(response.json())
    assert res.result.name == "name"


def test_get_repo_detail(mock_mongodb):
    client = TestClient(app)
    response = client.get("/api/repos/info/detail?name=name&owner=owner")
    assert response.status_code == 200
    res = GFIResponse[RepoDetail].parse_obj(response.json())
    assert res.result.name == "name"


def test_get_repo_language(mock_mongodb):
    client = TestClient(app)
    response = client.get("/api/repos/language")
    assert response.status_code == 200
    res = GFIResponse[List[str]].parse_obj(response.json())
    assert res.result[0] == "Python"


def test_get_repo_paged(mock_mongodb):
    client = TestClient(app)
    response = client.get("/api/repos/info/?start=0&length=3")
    assert response.status_code == 200
    res = GFIResponse[List[RepoDetail]].parse_obj(response.json())
    assert res.result[0].name == "name"

    # test language
    response = client.get("/api/repos/info/?start=0&length=3&lang=C++")
    assert response.status_code == 200
    res = GFIResponse[List[RepoDetail]].parse_obj(response.json())
    assert len(res.result) == 0

    # test sort
    response = client.get("/api/repos/info/?start=0&length=3&filter=popularity")
    assert response.status_code == 200
    res = GFIResponse[List[RepoDetail]].parse_obj(response.json())
    assert res.result[0].name == "name2"  # 2nd repo is the most popular

    response = client.get("/api/repos/info/?start=0&length=3&filter=gfis")
    assert response.status_code == 200
    res = GFIResponse[List[RepoDetail]].parse_obj(response.json())
    assert res.result[0].name == "name"  # 1st repo is the most GFIS

    response = client.get("/api/repos/info/?start=0&length=3&filter=median_issue_resolve_time")
    assert response.status_code == 200
    res = GFIResponse[List[RepoDetail]].parse_obj(response.json())
    assert res.result[0].name == "name2"  # 2nd repo median_issue_resolve_time is lower

    response = client.get("/api/repos/info/?start=0&length=3&filter=newcomer_friendly")
    assert response.status_code == 200
    res = GFIResponse[List[RepoDetail]].parse_obj(response.json())
    assert res.result[0].name == "name"  # 1st repo r_newcomer_resolved is higher


# # mongomock doesn't support text search
# def test_search_repo(mock_mongodb):
#     client = TestClient(app)
#     # search by name
#     response = client.get("/api/repos/info/search?repo=name")  
#     assert response.status_code == 200
#     res = GFIResponse[List[RepoDetail]].parse_obj(response.json())
    
#     # search by url
#     response = client.get("/api/repos/info/search?url=https://github.com/owner/name") 
#     assert response.status_code == 200
#     res = GFIResponse[List[RepoDetail]].parse_obj(response.json())
#     assert res.result[0].name == "name"

#     # search by description
#     response = client.get("/api/repos/info/search?repo=APP")
#     assert response.status_code == 200
#     res = GFIResponse[List[RepoDetail]].parse_obj(response.json())
#     assert res.result[0].name == "name"

# def test_get_add_repo(mock_mongodb):
#     client = TestClient(app)
#     response = client.post("/api/repos/add",
#         json={"repo": "name", "owner": "owner", "user": "chuchu"})
#     assert response.status_code == 200  # expect to succeed
#     res = GFIResponse[str].parse_obj(response.json())
#     assert "exists" in res.result
#     response = client.post("/api/repos/add", 
#         json={"repo": "name", "owner": "owner", "user": "nobody"})
#     assert response.status_code == 403   # expect to fail


# def test_get_update_config(mock_mongodb):
#     client = TestClient(app)
#     response = client.get("/api/repos/update/config?name=name&owner=owner")
#     assert response.status_code == 200
#     res = GFIResponse[Config].parse_obj(response.json())
#     assert res.result.update_config.task_id == "task_id"


# def test_force_repo(mock_mongodb):
#     client = TestClient(app)
#     response = client.post("/api/repos/update/",
#         json={"repo": "name", "owner": "owner", "user": "chuchu"})
#     assert response.status_code == 200  # expect to succeed
#     response = client.post("/api/repos/update/", 
#         json={"repo": "name", "owner": "owner", "user": "nobody"})
#     assert response.status_code == 403   # expect to fail


def test_get_repo_badge(mock_mongodb):
    client = TestClient(app)
    response = client.get("/api/repos/badge?name=name&owner=owner")
    assert response.status_code == 200
    # response should be a svg file
    assert "image/svg+xml" in response.headers["Content-Type"]
    response2 = client.get("/api/repos/badge/owner/name")
    assert response2.status_code == 200
    # response should be the same
    assert response.content == response2.content