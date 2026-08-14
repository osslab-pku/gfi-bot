import logging
from fastapi.testclient import TestClient
from gfibot.backend.server import app
from gfibot.backend.models import GFIResponse, ChatbotSessionResponse, ChatbotQueryResponse
from gfibot.collections import ChatbotSession


def test_create_chatbot_session_beginner(mock_mongodb):
    client = TestClient(app)
    response = client.post("/api/chatbot/session", json={"expertise_level": "beginner"})
    assert response.status_code == 200
    res = GFIResponse[ChatbotSessionResponse].parse_obj(response.json())
    assert res.result.expertise_level == "beginner"
    assert len(res.result.messages) == 1
    assert "beginner journey" in res.result.messages[0].content.lower()


def test_create_chatbot_session_advanced(mock_mongodb):
    client = TestClient(app)
    response = client.post(
        "/api/chatbot/session", json={"expertise_level": "advanced", "repo_name": "gfi-bot", "owner": "osslab-pku"}
    )
    assert response.status_code == 200
    res = GFIResponse[ChatbotSessionResponse].parse_obj(response.json())
    assert res.result.expertise_level == "advanced"
    assert res.result.repo_name == "gfi-bot"
    assert "gfi-bot" in res.result.messages[0].content


def test_create_chatbot_session_invalid_level(mock_mongodb):
    client = TestClient(app)
    response = client.post("/api/chatbot/session", json={"expertise_level": "expert_god_mode"})
    assert response.status_code == 400
    assert "Invalid expertise_level" in response.json()["detail"]


def test_get_chatbot_session(mock_mongodb):
    client = TestClient(app)
    create_res = client.post("/api/chatbot/session", json={"expertise_level": "intermediate"})
    sess_id = GFIResponse[ChatbotSessionResponse].parse_obj(create_res.json()).result.session_id

    get_res = client.get(f"/api/chatbot/session/{sess_id}")
    assert get_res.status_code == 200
    res = GFIResponse[ChatbotSessionResponse].parse_obj(get_res.json())
    assert res.result.session_id == sess_id
    assert res.result.expertise_level == "intermediate"


def test_get_nonexistent_session(mock_mongodb):
    client = TestClient(app)
    get_res = client.get("/api/chatbot/session/invalid_id_999")
    assert get_res.status_code == 404


def test_query_chatbot_gfi_info(mock_mongodb):
    client = TestClient(app)
    create_res = client.post("/api/chatbot/session", json={"expertise_level": "beginner"})
    sess_id = GFIResponse[ChatbotSessionResponse].parse_obj(create_res.json()).result.session_id

    query_res = client.post("/api/chatbot/query", json={"session_id": sess_id, "message": "What is GFI-Bot?"})
    assert query_res.status_code == 200
    res = GFIResponse[ChatbotQueryResponse].parse_obj(query_res.json())
    assert res.result.session_id == sess_id
    assert "good first issue" in res.result.reply.lower()
    assert len(res.result.history) == 3  # initial greeting + user query + assistant reply


def test_query_chatbot_config_advanced(mock_mongodb):
    client = TestClient(app)
    create_res = client.post("/api/chatbot/session", json={"expertise_level": "advanced"})
    sess_id = GFIResponse[ChatbotSessionResponse].parse_obj(create_res.json()).result.session_id

    query_res = client.post(
        "/api/chatbot/query", json={"session_id": sess_id, "message": "How do I configure gfibot.yaml?"}
    )
    assert query_res.status_code == 200
    res = GFIResponse[ChatbotQueryResponse].parse_obj(query_res.json())
    assert "newcomer_commit_threshold" in res.result.reply


def test_delete_chatbot_session(mock_mongodb):
    client = TestClient(app)
    create_res = client.post("/api/chatbot/session", json={"expertise_level": "beginner"})
    sess_id = GFIResponse[ChatbotSessionResponse].parse_obj(create_res.json()).result.session_id

    del_res = client.delete(f"/api/chatbot/session/{sess_id}")
    assert del_res.status_code == 200
    assert del_res.json()["result"] is True

    get_res = client.get(f"/api/chatbot/session/{sess_id}")
    assert get_res.status_code == 404
