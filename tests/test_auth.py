"""Authentication module tests."""

import pytest


def test_login_json_success(client):
    response = client.post(
        "/api/v1/auth/login/json",
        json={"username": "alice", "password": "alicepass123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20


def test_login_json_invalid_password(client):
    response = client.post(
        "/api/v1/auth/login/json",
        json={"username": "alice", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_login_oauth_form(client):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "adminpass123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_protected_route_requires_token(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_protected_route_with_token(client, user_token):
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "alice"


# reset_password endpoint intentionally has no unit test coverage (demo gap).
