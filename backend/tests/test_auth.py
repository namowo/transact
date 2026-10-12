import pytest
from httpx import AsyncClient


async def test_register_creates_user(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "Passw0rd!",
            "first_name": "New",
            "last_name": "User",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "newuser@example.com"
    assert "hashed_password" not in body


async def test_register_duplicate_email_rejected(client: AsyncClient, regular_user):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": regular_user.email,
            "password": "Passw0rd!",
            "first_name": "Dup",
            "last_name": "User",
        },
    )
    assert resp.status_code == 400


async def test_login_success_sets_cookie(client: AsyncClient, regular_user):
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": regular_user.email, "password": "Passw0rd!"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.cookies


async def test_login_wrong_password_rejected(client: AsyncClient, regular_user):
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": regular_user.email, "password": "wrong-password"},
    )
    assert resp.status_code == 401


async def test_login_unknown_email_rejected(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "nobody@example.com", "password": "Passw0rd!"},
    )
    assert resp.status_code == 401


async def test_login_inactive_user_rejected(client: AsyncClient, db_session, laboratory):
    from app.models.user import User
    from app.core.security import hash_password

    user = User(
        email="inactive@example.com",
        hashed_password=hash_password("Passw0rd!"),
        first_name="Inactive",
        last_name="User",
        is_active=False,
        is_verified=True,
        laboratory_id=laboratory.id,
    )
    db_session.add(user)
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "inactive@example.com", "password": "Passw0rd!"},
    )
    assert resp.status_code == 403


async def test_logout_clears_cookie(auth_client: AsyncClient):
    resp = await auth_client.post("/api/v1/auth/logout")
    assert resp.status_code == 204


async def test_setup_status_reports_needs_setup(client: AsyncClient):
    resp = await client.get("/api/v1/auth/setup-status")
    assert resp.status_code == 200
    assert resp.json()["needs_setup"] is True


async def test_setup_status_false_once_superuser_exists(client: AsyncClient, superuser):
    resp = await client.get("/api/v1/auth/setup-status")
    assert resp.status_code == 200
    assert resp.json()["needs_setup"] is False


async def test_setup_rejected_once_superuser_exists(client: AsyncClient, superuser):
    resp = await client.post(
        "/api/v1/auth/setup",
        json={
            "email": "second-admin@example.com",
            "password": "Passw0rd!",
            "first_name": "Second",
            "last_name": "Admin",
        },
    )
    assert resp.status_code == 403
