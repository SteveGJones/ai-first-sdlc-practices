"""Tests for MiniProject — deliberately incomplete for smoke test validation."""

import pytest
from src.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_list_users_returns_json(client):
    response = client.get("/users")
    assert response.status_code == 200
    assert response.content_type == "application/json"


def test_create_user(client):
    response = client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
    assert response.status_code == 201


# DELIBERATE GAP: No test for DELETE /users/<id>
# DELIBERATE GAP: No test for SQL injection vulnerability
# DELIBERATE GAP: No test for missing input validation
