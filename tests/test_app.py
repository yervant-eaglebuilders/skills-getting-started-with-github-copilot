import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client(monkeypatch):
    test_activities = {
        "Chess Club": {
            "description": "Learn chess",
            "schedule": "Fridays",
            "max_participants": 12,
            "participants": ["existing@example.com"],
        }
    }
    monkeypatch.setattr(app_module, "activities", test_activities)
    return TestClient(app_module.app)


def test_root_redirects_to_frontend(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()["Chess Club"]["participants"] == ["existing@example.com"]


def test_signup_adds_participant(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "new@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Signed up new@example.com for Chess Club"}
    activities_response = client.get("/activities")
    assert "new@example.com" in activities_response.json()["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "existing@example.com"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    participants = client.get("/activities").json()["Chess Club"]["participants"]
    assert participants == ["existing@example.com"]


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "new@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "existing@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Removed existing@example.com from Chess Club"}
    participants = client.get("/activities").json()["Chess Club"]["participants"]
    assert "existing@example.com" not in participants


def test_unregister_rejects_unregistered_participant(client):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "missing@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown Club/signup",
        params={"email": "new@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"