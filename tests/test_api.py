import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client(monkeypatch):
    activities = {
        "Chess Club": {
            "description": "Learn chess",
            "schedule": "Fridays",
            "max_participants": 12,
            "participants": ["alex@example.edu"],
        },
        "Art Club": {
            "description": "Explore art",
            "schedule": "Wednesdays",
            "max_participants": 18,
            "participants": [],
        },
    }
    monkeypatch.setattr(app_module, "activities", activities)

    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_frontend(client):
    # Arrange
    redirect_path = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == redirect_path


def test_get_activities_returns_available_activities(client):
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert expected_activity in response.json()
    assert response.json()[expected_activity]["participants"] == ["alex@example.edu"]


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Art Club"
    email = "sam@example.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    activities = client.get("/activities").json()
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "alex@example.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "sam@example.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_unregisters_student(client):
    # Arrange
    activity_name = "Chess Club"
    email = "alex@example.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    activities = client.get("/activities").json()
    assert email not in activities[activity_name]["participants"]


def test_remove_participant_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": "alex@example.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_rejects_unregistered_email(client):
    # Arrange
    activity_name = "Chess Club"
    email = "unregistered@example.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"