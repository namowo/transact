import pytest
from httpx import AsyncClient

from app.api.routers import study as study_router
from app.core.notification_catalog import NotificationType
from app.core.security import create_access_token
from app.models.laboratory import Laboratory
from app.models.study import Study
from app.models.user import User
from app.services.mail import main as mail_main
from app.services.mail.messages import (
    send_new_lab_requested_mail,
    send_new_membership_request_mail,
)


def _login(client: AsyncClient, user: User) -> AsyncClient:
    client.cookies.update({"access_token": create_access_token(subject=str(user.id))})
    return client


@pytest.fixture
def sent_mails(monkeypatch) -> list[tuple[str, str]]:
    """(recipient, template) of every mail, rendered but not sent."""
    sent: list[tuple[str, str]] = []

    async def fake_send_mail(subject, to_recipient, template_name, template_values):
        mail_main.get_content(template_name, template_values)
        sent.append((to_recipient, template_name))

    for module in ("lab_membership", "lab_requests", "study_quality_check"):
        monkeypatch.setattr(
            f"app.services.mail.messages.{module}.send_mail", fake_send_mail
        )
    return sent


async def _types(client: AsyncClient, user: User) -> list[str]:
    resp = await _login(client, user).get("/api/v1/users/me/notification-types")
    assert resp.status_code == 200, resp.text
    return [t["key"] for t in resp.json()]


async def test_types_follow_permissions(
    client: AsyncClient, regular_user, data_entrant, lab_admin, superuser
):
    assert await _types(client, regular_user) == []
    assert await _types(client, data_entrant) == ["study_quality_checked", "study_changes_requested"]
    assert "lab_membership_request" in await _types(client, lab_admin)
    assert "laboratory_request" not in await _types(client, lab_admin)
    assert "laboratory_request" in await _types(client, superuser)


async def test_settings_defaults_and_partial_update(lab_admin_client: AsyncClient):
    resp = await lab_admin_client.get("/api/v1/users/me")
    settings = resp.json()["notification_settings"]
    assert settings["lab_membership_request"] == {"email": True, "browser": False}
    assert settings["study_quality_checked"] == {"email": True}

    resp = await lab_admin_client.patch(
        "/api/v1/users/me",
        json={"notification_settings": {"lab_membership_request": {"browser": True}}},
    )
    assert resp.status_code == 200, resp.text
    resp = await lab_admin_client.patch(
        "/api/v1/users/me",
        json={"notification_settings": {"lab_membership_request": {"email": False}}},
    )
    settings = resp.json()["notification_settings"]
    assert settings["lab_membership_request"] == {"email": False, "browser": True}
    assert settings["laboratory_request"] == {"email": True, "browser": False}


@pytest.mark.parametrize(
    "payload",
    [
        {"study_quality_checked": {"browser": True}},
        {"unknown_type": {"email": True}},
        {"lab_membership_request": {"sms": True}},
    ],
)
async def test_rejects_unsupported_settings(auth_client: AsyncClient, payload):
    resp = await auth_client.patch(
        "/api/v1/users/me", json={"notification_settings": payload}
    )
    assert resp.status_code == 422


async def test_review_mails_respect_settings_and_permissions(
    sent_mails, lab_admin: User, regular_user: User, laboratory
):
    await send_new_membership_request_mail(lab_admin, regular_user, laboratory)
    assert sent_mails == [(lab_admin.email, "new-membership-request.html")]

    sent_mails.clear()
    lab_admin.notification_settings = {"lab_membership_request": {"email": False}}
    await send_new_membership_request_mail(lab_admin, regular_user, laboratory)
    assert sent_mails == []

    # Without the permission, a stored "on" doesn't count.
    regular_user.notification_settings = {"laboratory_request": {"email": True}}
    assert not regular_user.wants_notification(NotificationType.LABORATORY_REQUEST, "email")
    await send_new_lab_requested_mail(regular_user, laboratory, lab_admin)
    assert sent_mails == []


async def test_quality_check_notifies_data_entrants_of_the_lab(
    sent_mails,
    superuser_client: AsyncClient,
    db_session,
    laboratory: Laboratory,
    data_entrant: User,
    regular_user: User,
):
    study = Study(title="A study", laboratory_id=laboratory.id, published=False)
    db_session.add(study)
    await db_session.commit()

    resp = await superuser_client.post(f"/api/v1/studies/{study.id}/quality-check")
    assert resp.status_code == 200, resp.text
    # Not the checker, not members without data entry.
    assert sent_mails == [(data_entrant.email, "study-quality-checked.html")]


async def test_quality_check_mail_can_be_turned_off(
    sent_mails,
    superuser_client: AsyncClient,
    db_session,
    laboratory: Laboratory,
    data_entrant: User,
):
    data_entrant.notification_settings = {"study_quality_checked": {"email": False}}
    study = Study(title="A study", laboratory_id=laboratory.id, published=False)
    db_session.add_all([data_entrant, study])
    await db_session.commit()

    resp = await superuser_client.post(f"/api/v1/studies/{study.id}/quality-check")
    assert resp.status_code == 200, resp.text
    assert sent_mails == []
