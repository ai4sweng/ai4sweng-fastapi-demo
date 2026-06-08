"""User management module tests."""

import pytest

from app.users import service as user_service
from app.users.schemas import UserCreate


def test_register_user(client):
    response = client.post(
        "/api/v1/users",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "bobpass123",
            "role": "user",
        },
    )
    assert response.status_code == 201
    assert response.json()["username"] == "bob"


def test_register_duplicate_username(client):
    payload = {
        "username": "carol",
        "email": "carol@example.com",
        "password": "carolpass123",
        "role": "user",
    }
    assert client.post("/api/v1/users", json=payload).status_code == 201
    assert client.post("/api/v1/users", json=payload).status_code == 400


def test_list_users_requires_admin(client, user_token):
    response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403


def test_list_users_as_admin(client, admin_token):
    response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) >= 2


def test_search_users(client, admin_token):
    response = client.get(
        "/api/v1/users/search",
        params={"q": "ali"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    usernames = [row["username"] for row in response.json()]
    assert "alice" in usernames


def test_get_user_profile_with_profile(client, db_session):
    alice = user_service.get_user_by_username(db_session, "alice")
    response = client.get(f"/api/v1/users/{alice.id}/profile")
    assert response.status_code == 200
    assert response.json()["display_name"] == "Alice"


def test_get_user_profile_without_profile_returns_error(client, db_session):
    """Exposes null-pointer risk when profile row is missing."""
    user = user_service.create_user(
        db_session,
        UserCreate(
            username="noprofile",
            email="noprofile@example.com",
            password="noprofile1",
        ),
    )
    response = client.get(f"/api/v1/users/{user.id}/profile")
    # AttributeError is caught and mapped to 404 — still a logic bug in service layer.
    assert response.status_code == 404


def test_update_own_profile(client, user_token):
    me = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {user_token}"},
    ).json()
    response = client.put(
        f"/api/v1/users/{me['id']}/profile",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"bio": "Updated bio"},
    )
    assert response.status_code == 200
    assert response.json()["bio"] == "Updated bio"
