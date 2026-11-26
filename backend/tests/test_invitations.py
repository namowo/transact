import pytest
from httpx import AsyncClient

from app.api.routers import users as users_router
from app.models.laboratory import Laboratory
from app.models.user import User
from app.models.user_group import UserGroup


@pytest.fixture
def sent_invitations(monkeypatch) -> list[tuple[str, str]]:
    """(email, raw token) of every invitation mail, instead of sending it."""
    sent: list[tuple[str, str]] = []

    async def fake_send(user, inviter, token):
        sent.append((user.email, token))

    monkeypatch.setattr(users_router, "send_invitation_mail", fake_send)
    return sent


def invite_payload(**overrides) -> dict:
    payload = {
        "email": "Invitee@Example.com",
        "first_name": "Ina",
        "last_name": "Vitee",
    }
    payload.update(overrides)
    return payload


async def test_invite_requires_managing_members(auth_client: AsyncClient, sent_invitations):
    resp = await auth_client.post("/api/v1/users/invite", json=invite_payload())
    assert resp.status_code == 403
    assert sent_invitations == []


async def test_admin_invites_user_who_accepts(
    superuser_client: AsyncClient,
    laboratory: Laboratory,
    data_entry_group: UserGroup,
    sent_invitations,
):
    resp = await superuser_client.post(
        "/api/v1/users/invite",
        json=invite_payload(
            laboratory_id=str(laboratory.id), group_ids=[str(data_entry_group.id)]
        ),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["email"] == "invitee@example.com"
    assert body["invitation_pending"] is True
    assert body["is_verified"] is False
    assert body["laboratory_id"] == str(laboratory.id)
    assert [g["id"] for g in body["groups"]] == [str(data_entry_group.id)]
    [(email, token)] = sent_invitations
    assert email == "invitee@example.com"

    superuser_client.cookies.clear()
    resp = await superuser_client.post(
        "/api/v1/auth/accept-invitation", json={"token": token, "password": "Passw0rd!"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["invitation_pending"] is False
    assert resp.json()["is_verified"] is True
    assert "access_token" in resp.cookies

    # Single use.
    resp = await superuser_client.post(
        "/api/v1/auth/accept-invitation", json={"token": token, "password": "Passw0rd!"}
    )
    assert resp.status_code == 400

    resp = await superuser_client.post(
        "/api/v1/auth/login",
        data={"username": "invitee@example.com", "password": "Passw0rd!"},
    )
    assert resp.status_code == 200


async def test_invite_existing_email_rejected(
    superuser_client: AsyncClient, regular_user: User, sent_invitations
):
    resp = await superuser_client.post(
        "/api/v1/users/invite", json=invite_payload(email=regular_user.email)
    )
    assert resp.status_code == 400
    assert sent_invitations == []


async def test_lab_admin_invites_into_own_laboratory(
    lab_admin_client: AsyncClient, laboratory: Laboratory, sent_invitations
):
    resp = await lab_admin_client.post("/api/v1/users/invite", json=invite_payload())
    assert resp.status_code == 201, resp.text
    assert resp.json()["laboratory_id"] == str(laboratory.id)


async def test_lab_admin_cannot_invite_into_other_laboratory(
    lab_admin_client: AsyncClient, db_session, sent_invitations
):
    other = Laboratory(
        laboratory_name="Other Lab", institutional_affiliation="Elsewhere", city="", country=""
    )
    db_session.add(other)
    await db_session.commit()

    resp = await lab_admin_client.post(
        "/api/v1/users/invite", json=invite_payload(laboratory_id=str(other.id))
    )
    assert resp.status_code == 403
    assert sent_invitations == []


async def test_lab_admin_cannot_grant_groups_beyond_own_permissions(
    lab_admin_client: AsyncClient, superuser: User, sent_invitations
):
    admin_group = superuser.groups[0]
    resp = await lab_admin_client.post(
        "/api/v1/users/invite", json=invite_payload(group_ids=[str(admin_group.id)])
    )
    assert resp.status_code == 403
    assert sent_invitations == []


async def test_resend_and_withdraw_invitation(
    lab_admin_client: AsyncClient, regular_user: User, sent_invitations
):
    resp = await lab_admin_client.post("/api/v1/users/invite", json=invite_payload())
    invitee_id = resp.json()["id"]

    resp = await lab_admin_client.post(f"/api/v1/users/{invitee_id}/resend-invitation")
    assert resp.status_code == 200
    assert len(sent_invitations) == 2
    first_token, second_token = (token for _, token in sent_invitations)

    # Resending invalidates the earlier link.
    client_cookies = dict(lab_admin_client.cookies)
    lab_admin_client.cookies.clear()
    resp = await lab_admin_client.post(
        "/api/v1/auth/accept-invitation",
        json={"token": first_token, "password": "Passw0rd!"},
    )
    assert resp.status_code == 400
    lab_admin_client.cookies.update(client_cookies)

    # Lab admins can't delete members, only withdraw invitations.
    resp = await lab_admin_client.delete(f"/api/v1/users/{regular_user.id}")
    assert resp.status_code == 403
    resp = await lab_admin_client.delete(f"/api/v1/users/{invitee_id}")
    assert resp.status_code == 204

    resp = await lab_admin_client.post(
        "/api/v1/auth/accept-invitation",
        json={"token": second_token, "password": "Passw0rd!"},
    )
    assert resp.status_code == 400


async def test_resend_rejected_once_accepted(
    superuser_client: AsyncClient, regular_user: User, sent_invitations
):
    resp = await superuser_client.post(f"/api/v1/users/{regular_user.id}/resend-invitation")
    assert resp.status_code == 400


async def test_password_reset_accepts_pending_invitation(
    superuser_client: AsyncClient, sent_invitations, monkeypatch
):
    from app.api.routers import auth as auth_router

    resets: list[str] = []

    async def fake_reset(user, token):
        resets.append(token)

    monkeypatch.setattr(auth_router, "send_reset_password_mail", fake_reset)

    await superuser_client.post("/api/v1/users/invite", json=invite_payload())
    await superuser_client.post(
        "/api/v1/auth/forgot-password", json={"email": "invitee@example.com"}
    )
    resp = await superuser_client.post(
        "/api/v1/auth/reset-password",
        json={"token": resets[0], "new_password": "Passw0rd!"},
    )
    assert resp.status_code == 200

    resp = await superuser_client.post(
        "/api/v1/auth/login",
        data={"username": "invitee@example.com", "password": "Passw0rd!"},
    )
    assert resp.status_code == 200
    assert resp.json()["invitation_pending"] is False
    assert resp.json()["is_verified"] is True
