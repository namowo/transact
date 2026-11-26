import pytest
from httpx import AsyncClient

from app.api.routers import privacy_policy as privacy_policy_router
from app.models.user import User

BASE = "/api/v1/privacy-policy"


@pytest.fixture
def sent_mails(monkeypatch) -> list[str]:
    """Emails told about a new policy, instead of sending them."""
    sent: list[str] = []

    async def fake_send(recipients):
        sent.extend(email for email, _, _ in recipients)

    monkeypatch.setattr(privacy_policy_router, "send_privacy_policy_updated_mails", fake_send)
    return sent


async def publish(client: AsyncClient, text: str, notify: bool = True) -> dict:
    resp = await client.post(f"{BASE}/versions", json={"mode": "text", "text": text})
    assert resp.status_code == 201, resp.text
    resp = await client.post(
        f"{BASE}/versions/{resp.json()['id']}/publish", json={"notify_users": notify}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_no_policy_by_default(client: AsyncClient):
    resp = await client.get(BASE)
    assert resp.status_code == 200
    assert resp.json() is None


async def test_only_managers_create_drafts(auth_client: AsyncClient):
    resp = await auth_client.post(f"{BASE}/versions", json={"text": "<p>x</p>"})
    assert resp.status_code == 403


async def test_draft_lifecycle(superuser_client: AsyncClient, sent_mails):
    resp = await superuser_client.post(f"{BASE}/versions", json={"text": "<p>v1</p>"})
    assert resp.status_code == 201
    draft = resp.json()
    assert draft["status"] == "draft"
    assert draft["version"] is None

    # Drafts aren't public, and only one exists at a time.
    assert (await superuser_client.get(BASE)).json() is None
    resp = await superuser_client.post(f"{BASE}/versions", json={})
    assert resp.status_code == 409

    resp = await superuser_client.patch(
        f"{BASE}/versions/{draft['id']}", json={"text": "<p>v1 edited</p>"}
    )
    assert resp.status_code == 200
    assert resp.json()["text"] == "<p>v1 edited</p>"

    resp = await superuser_client.post(
        f"{BASE}/versions/{draft['id']}/publish", json={"notify_users": True}
    )
    assert resp.status_code == 200, resp.text
    published = resp.json()
    assert published["status"] == "active"
    assert published["version"] == 1
    assert sent_mails == ["admin@example.com"]

    active = (await superuser_client.get(BASE)).json()
    assert active["id"] == draft["id"]
    assert active["text"] == "<p>v1 edited</p>"

    # Published versions are frozen.
    resp = await superuser_client.patch(
        f"{BASE}/versions/{draft['id']}", json={"text": "<p>sneaky</p>"}
    )
    assert resp.status_code == 409
    resp = await superuser_client.delete(f"{BASE}/versions/{draft['id']}")
    assert resp.status_code == 409


async def test_new_version_starts_from_active_and_history_is_kept(
    superuser_client: AsyncClient, sent_mails
):
    v1 = await publish(superuser_client, "<p>v1</p>")
    sent_mails.clear()

    resp = await superuser_client.post(f"{BASE}/versions", json={})
    draft = resp.json()
    assert draft["text"] == "<p>v1</p>"

    resp = await superuser_client.post(
        f"{BASE}/versions/{draft['id']}/publish", json={"notify_users": False}
    )
    assert resp.json()["version"] == 2
    assert sent_mails == []

    versions = (await superuser_client.get(f"{BASE}/versions")).json()
    assert [(v["version"], v["status"]) for v in versions] == [
        (2, "active"),
        (1, "archived"),
    ]

    # Old versions stay readable by anyone.
    superuser_client.cookies.clear()
    resp = await superuser_client.get(f"{BASE}/versions/{v1['id']}")
    assert resp.status_code == 200
    assert resp.json()["text"] == "<p>v1</p>"


async def test_discard_draft(superuser_client: AsyncClient):
    draft = (await superuser_client.post(f"{BASE}/versions", json={})).json()
    resp = await superuser_client.delete(f"{BASE}/versions/{draft['id']}")
    assert resp.status_code == 204
    assert (await superuser_client.get(f"{BASE}/versions")).json() == []


async def test_drafts_hidden_from_others(
    superuser_client: AsyncClient, client: AsyncClient
):
    draft = (await superuser_client.post(f"{BASE}/versions", json={})).json()
    superuser_client.cookies.clear()
    resp = await client.get(f"{BASE}/versions/{draft['id']}")
    assert resp.status_code == 404


async def test_cannot_publish_empty(superuser_client: AsyncClient):
    draft = (await superuser_client.post(f"{BASE}/versions", json={"text": " "})).json()
    resp = await superuser_client.post(
        f"{BASE}/versions/{draft['id']}/publish", json={}
    )
    assert resp.status_code == 400


async def test_user_must_accept_new_version(
    superuser_client: AsyncClient, client: AsyncClient, regular_user: User, sent_mails
):
    from tests.conftest import auth_headers

    v1 = await publish(superuser_client, "<p>v1</p>")
    superuser_client.cookies.clear()
    headers = auth_headers(regular_user)

    me = (await client.get("/api/v1/users/me", headers=headers)).json()
    assert me["accepted_privacy_policy_ids"] == []

    resp = await client.post(
        f"{BASE}/consent", json={"privacy_policy_id": v1["id"]}, headers=headers
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["accepted_privacy_policy_ids"] == [v1["id"]]

    # Accepting twice is harmless.
    resp = await client.post(
        f"{BASE}/consent", json={"privacy_policy_id": v1["id"]}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["accepted_privacy_policy_ids"] == [v1["id"]]


async def test_only_active_version_can_be_accepted(
    client: AsyncClient, superuser: User, regular_user: User, sent_mails
):
    from tests.conftest import auth_headers

    admin = auth_headers(superuser)
    user = auth_headers(regular_user)

    async def publish_as_admin(text: str) -> dict:
        draft = (
            await client.post(f"{BASE}/versions", json={"text": text}, headers=admin)
        ).json()
        return (
            await client.post(
                f"{BASE}/versions/{draft['id']}/publish", json={}, headers=admin
            )
        ).json()

    v1 = await publish_as_admin("<p>v1</p>")
    v2 = await publish_as_admin("<p>v2</p>")

    resp = await client.post(
        f"{BASE}/consent", json={"privacy_policy_id": v1["id"]}, headers=user
    )
    assert resp.status_code == 409
    resp = await client.post(
        f"{BASE}/consent", json={"privacy_policy_id": v2["id"]}, headers=user
    )
    assert resp.status_code == 200
    assert resp.json()["accepted_privacy_policy_ids"] == [v2["id"]]

    versions = (await client.get(f"{BASE}/versions", headers=admin)).json()
    assert {v["version"]: v["consent_count"] for v in versions} == {2: 1, 1: 0}


REGISTRATION = {
    "email": "new@example.com",
    "password": "Passw0rd!",
    "first_name": "New",
    "last_name": "User",
}


async def test_register_records_consent(
    client: AsyncClient, superuser: User, sent_mails, monkeypatch
):
    from tests.conftest import auth_headers

    admin = auth_headers(superuser)
    draft = (
        await client.post(f"{BASE}/versions", json={"text": "<p>v1</p>"}, headers=admin)
    ).json()
    await client.post(f"{BASE}/versions/{draft['id']}/publish", json={}, headers=admin)

    resp = await client.post("/api/v1/auth/register", json=REGISTRATION)
    assert resp.status_code == 409

    resp = await client.post(
        "/api/v1/auth/register", json={**REGISTRATION, "privacy_policy_id": draft["id"]}
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["accepted_privacy_policy_ids"] == [draft["id"]]
