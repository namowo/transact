import uuid

import pytest
from httpx import AsyncClient

from app.models.user import User


async def test_read_me_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401


async def test_read_me_returns_current_user(auth_client: AsyncClient, regular_user: User):
    resp = await auth_client.get("/api/v1/users/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == regular_user.email


async def test_list_users_requires_superuser(auth_client: AsyncClient):
    resp = await auth_client.get("/api/v1/users")
    assert resp.status_code == 403


async def test_list_users_as_superuser(superuser_client: AsyncClient, regular_user: User):
    resp = await superuser_client.get("/api/v1/users")
    assert resp.status_code == 200
    emails = {u["email"] for u in resp.json()}
    assert regular_user.email in emails


async def test_change_password_rejects_wrong_current_password(
    auth_client: AsyncClient,
):
    resp = await auth_client.post(
        "/api/v1/users/me/change-password",
        json={"current_password": "wrong", "new_password": "NewPassw0rd!"},
    )
    assert resp.status_code == 400


async def test_change_password_succeeds_with_correct_current_password(
    auth_client: AsyncClient,
):
    resp = await auth_client.post(
        "/api/v1/users/me/change-password",
        json={"current_password": "Passw0rd!", "new_password": "NewPassw0rd!"},
    )
    assert resp.status_code == 200


async def test_assigning_groups_requires_managing_members(
    auth_client: AsyncClient, regular_user: User
):
    resp = await auth_client.put(
        f"/api/v1/users/{regular_user.id}/groups", json={"group_ids": []}
    )
    assert resp.status_code == 403


async def test_delete_own_account_rejected(superuser_client: AsyncClient, superuser: User):
    resp = await superuser_client.delete(f"/api/v1/users/{superuser.id}")
    assert resp.status_code == 400


async def test_delete_other_user_as_superuser(
    superuser_client: AsyncClient, regular_user: User
):
    resp = await superuser_client.delete(f"/api/v1/users/{regular_user.id}")
    assert resp.status_code == 204


async def test_delete_user_requires_superuser(auth_client: AsyncClient, regular_user: User):
    resp = await auth_client.delete(f"/api/v1/users/{uuid.uuid4()}")
    assert resp.status_code == 403


async def test_complete_tour_is_recorded_once(auth_client: AsyncClient):
    resp = await auth_client.get("/api/v1/users/me")
    assert resp.json()["completed_tours"] == []

    for _ in range(2):
        resp = await auth_client.post("/api/v1/users/me/completed-tours/onboarding")
        assert resp.status_code == 200
    assert resp.json()["completed_tours"] == ["onboarding"]

    resp = await auth_client.post("/api/v1/users/me/completed-tours/new-study")
    assert resp.json()["completed_tours"] == ["onboarding", "new-study"]


async def test_complete_unknown_tour_rejected(auth_client: AsyncClient):
    resp = await auth_client.post("/api/v1/users/me/completed-tours/nope")
    assert resp.status_code == 422
