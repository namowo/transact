import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import encryption, totp
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User
from app.crud.webauthn_credential import crud_webauthn_credential
from app.models.webauthn_credential import WebAuthnCredential

LOGIN = "/api/v1/auth/login"
LOGIN_2FA = "/api/v1/auth/login/two-factor"
SETUP = "/api/v1/auth/two-factor/totp/setup"
ENABLE = "/api/v1/auth/two-factor/totp/enable"
DISABLE = "/api/v1/auth/two-factor/totp/disable"
RECOVERY = "/api/v1/auth/two-factor/recovery-codes"
ME = "/api/v1/users/me"


@pytest.fixture
def two_factor_required(monkeypatch):
    monkeypatch.setattr(settings, "TWO_FACTOR_REQUIRED", True)


def use_session(client: AsyncClient, resp) -> None:
    """Carry the session cookie over (it's Secure, so httpx won't over http)."""
    client.cookies.set("access_token", resp.cookies["access_token"])


async def password_login(client: AsyncClient, email: str = "user@example.com"):
    return await client.post(LOGIN, data={"username": email, "password": "Passw0rd!"})


async def enable_totp(client: AsyncClient) -> tuple[str, list[str]]:
    resp = await client.post(SETUP)
    assert resp.status_code == 200, resp.text
    secret = resp.json()["secret"]
    assert resp.json()["provisioning_uri"].startswith("otpauth://totp/")
    resp = await client.post(ENABLE, json={"code": totp.code_at(secret, totp.current_step())})
    assert resp.status_code == 200, resp.text
    use_session(client, resp)
    return secret, resp.json()["recovery_codes"]


async def add_passkey(db_session: AsyncSession, user: User) -> None:
    db_session.add(
        WebAuthnCredential(
            user_id=user.id, credential_id=f"cred-{user.id}", public_key=b"key"
        )
    )
    await db_session.commit()


# --- TOTP primitives -------------------------------------------------------


def test_totp_matches_rfc_6238_vector():
    # RFC 6238 appendix B, SHA-1, T = 59s -> 94287082 (8 digits; we use 6).
    secret = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"  # "12345678901234567890"
    assert totp.code_at(secret, 59 // 30) == "287082"
    assert totp.verify(secret, "287 082", now=59) == 1


def test_totp_refuses_used_steps():
    secret = totp.generate_secret()
    code = totp.code_at(secret, totp.current_step())
    step = totp.verify(secret, code)
    assert step is not None
    assert totp.verify(secret, code, last_used_step=step) is None


# --- Policy ----------------------------------------------------------------


async def test_config_reports_policy(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "REGISTRATION_ENABLED", False)
    resp = await client.get("/api/v1/auth/config")
    assert resp.json() == {
        "registration_enabled": False,
        "invitations_enabled": True,
        "two_factor_required": False,
    }


async def test_registration_can_be_disabled(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "REGISTRATION_ENABLED", False)
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@example.com",
            "password": "Passw0rd!",
            "first_name": "New",
            "last_name": "User",
        },
    )
    assert resp.status_code == 403


async def test_invitations_can_be_disabled(superuser_client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "INVITATIONS_ENABLED", False)
    resp = await superuser_client.post(
        "/api/v1/users/invite",
        json={"email": "invitee@example.com", "first_name": "I", "last_name": "V"},
    )
    assert resp.status_code == 403
    resp = await superuser_client.post(
        "/api/v1/auth/accept-invitation", json={"token": "x", "password": "Passw0rd!"}
    )
    assert resp.status_code == 403


# --- Authenticator app sign-in ---------------------------------------------


async def test_totp_login_flow(auth_client: AsyncClient):
    secret, recovery_codes = await enable_totp(auth_client)
    assert len(recovery_codes) == totp.RECOVERY_CODE_COUNT
    auth_client.cookies.clear()

    resp = await password_login(auth_client)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["two_factor_required"] is True
    assert body["methods"] == ["totp"]
    assert "access_token" not in resp.cookies

    # The login token isn't a session.
    auth_client.cookies.set("access_token", body["login_token"])
    assert (await auth_client.get(ME)).status_code == 401
    auth_client.cookies.clear()

    resp = await auth_client.post(
        LOGIN_2FA, json={"login_token": body["login_token"], "code": "000000"}
    )
    # (A wrong code, unless we hit the 1 in a million.)
    if resp.status_code == 200:
        return
    assert resp.status_code == 400

    # The code from enabling was used already, so take the next one.
    code = totp.code_at(secret, totp.current_step() + 1)
    resp = await auth_client.post(
        LOGIN_2FA, json={"login_token": body["login_token"], "code": code}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["totp_enabled"] is True
    use_session(auth_client, resp)
    assert (await auth_client.get(ME)).status_code == 200

    # Not twice.
    resp = await auth_client.post(
        LOGIN_2FA, json={"login_token": body["login_token"], "code": code}
    )
    assert resp.status_code == 400


async def test_recovery_code_is_single_use(auth_client: AsyncClient):
    _, recovery_codes = await enable_totp(auth_client)
    auth_client.cookies.clear()
    login_token = (await password_login(auth_client)).json()["login_token"]

    resp = await auth_client.post(
        LOGIN_2FA, json={"login_token": login_token, "code": recovery_codes[0].upper()}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["recovery_codes_remaining"] == totp.RECOVERY_CODE_COUNT - 1

    resp = await auth_client.post(
        LOGIN_2FA, json={"login_token": login_token, "code": recovery_codes[0]}
    )
    assert resp.status_code == 400


async def test_wrong_codes_lock_the_code_step(auth_client: AsyncClient):
    secret, _ = await enable_totp(auth_client)
    auth_client.cookies.clear()
    login_token = (await password_login(auth_client)).json()["login_token"]

    for _ in range(5):
        resp = await auth_client.post(
            LOGIN_2FA, json={"login_token": login_token, "code": "wrong-code"}
        )
        assert resp.status_code == 400
    code = totp.code_at(secret, totp.current_step() + 1)
    resp = await auth_client.post(LOGIN_2FA, json={"login_token": login_token, "code": code})
    assert resp.status_code == 429


async def test_disable_totp_needs_password_and_code(auth_client: AsyncClient):
    secret, recovery_codes = await enable_totp(auth_client)
    resp = await auth_client.post(
        DISABLE, json={"current_password": "wrong", "code": recovery_codes[0]}
    )
    assert resp.status_code == 400
    resp = await auth_client.post(
        DISABLE, json={"current_password": "Passw0rd!", "code": recovery_codes[0]}
    )
    assert resp.status_code == 204
    assert (await auth_client.get(ME)).json()["totp_enabled"] is False


async def test_regenerate_recovery_codes(auth_client: AsyncClient):
    _, old_codes = await enable_totp(auth_client)
    resp = await auth_client.post(RECOVERY, json={"code": old_codes[0]})
    assert resp.status_code == 200
    new_codes = resp.json()["recovery_codes"]
    assert set(new_codes).isdisjoint(old_codes)


# --- Two-factor authentication required ------------------------------------


async def test_required_two_factor_limits_session_to_setup(
    client: AsyncClient, regular_user: User, two_factor_required
):
    resp = await password_login(client)
    assert resp.status_code == 200, resp.text
    assert resp.json()["two_factor_setup_required"] is True
    use_session(client, resp)

    me = await client.get(ME)
    assert me.status_code == 200
    assert me.json()["two_factor_setup_required"] is True
    resp = await client.get("/api/v1/auth/api-keys")
    assert resp.status_code == 403

    secret, _ = await enable_totp(client)
    # Enabling upgraded the session.
    me = await client.get(ME)
    assert me.json()["two_factor_setup_required"] is False
    assert (await client.get("/api/v1/auth/api-keys")).status_code == 200


async def test_required_two_factor_rejects_old_session_of_enrolled_user(
    auth_client: AsyncClient, regular_user: User, monkeypatch
):
    await enable_totp(auth_client)
    monkeypatch.setattr(settings, "TWO_FACTOR_REQUIRED", True)
    # A session without a second factor, e.g. from before it was required.
    auth_client.cookies.set("access_token", create_access_token(str(regular_user.id)))
    assert (await auth_client.get(ME)).status_code == 401
    assert (await auth_client.post(SETUP)).status_code == 401


async def test_required_two_factor_passkey_user_cannot_use_password_alone(
    client: AsyncClient, db_session: AsyncSession, regular_user: User, two_factor_required
):
    await add_passkey(db_session, regular_user)
    resp = await password_login(client)
    assert resp.status_code == 200
    assert resp.json() == {
        "two_factor_required": True,
        "login_token": None,
        "methods": ["passkey"],
    }
    assert "access_token" not in resp.cookies


async def test_cannot_remove_last_factor_when_required(
    auth_client: AsyncClient, two_factor_required, regular_user: User
):
    # Enrolled during setup, so the session is a two-factor one.
    auth_client.cookies.clear()
    use_session(auth_client, await password_login(auth_client))
    _, recovery_codes = await enable_totp(auth_client)
    resp = await auth_client.post(
        DISABLE, json={"current_password": "Passw0rd!", "code": recovery_codes[0]}
    )
    assert resp.status_code == 400


async def test_admin_resets_two_factor(
    superuser_client: AsyncClient,
    db_session: AsyncSession,
    regular_user: User,
):
    await add_passkey(db_session, regular_user)
    regular_user.totp_secret = totp.generate_secret()
    await db_session.commit()

    resp = await superuser_client.post(f"/api/v1/users/{regular_user.id}/reset-two-factor")
    assert resp.status_code == 200, resp.text
    assert resp.json()["totp_enabled"] is False
    assert not await crud_webauthn_credential.exists_for_user(db_session, regular_user)


async def test_reset_two_factor_needs_managing_users(
    auth_client: AsyncClient, regular_user: User
):
    resp = await auth_client.post(f"/api/v1/users/{regular_user.id}/reset-two-factor")
    assert resp.status_code == 403


# --- Encrypted secrets -----------------------------------------------------


async def test_totp_secret_is_stored_encrypted(
    auth_client: AsyncClient, db_session: AsyncSession, regular_user: User
):
    secret, _ = await enable_totp(auth_client)
    await db_session.refresh(regular_user)
    assert regular_user.totp_secret is not None
    assert secret not in regular_user.totp_secret
    assert encryption.decrypt(regular_user.totp_secret) == secret


async def test_undecryptable_secret_still_accepts_recovery_codes(
    auth_client: AsyncClient, db_session: AsyncSession, regular_user: User
):
    _, recovery_codes = await enable_totp(auth_client)
    regular_user.totp_secret = "not-encrypted-with-this-key"
    await db_session.commit()
    auth_client.cookies.clear()
    login_token = (await password_login(auth_client)).json()["login_token"]
    resp = await auth_client.post(
        LOGIN_2FA, json={"login_token": login_token, "code": recovery_codes[0]}
    )
    assert resp.status_code == 200, resp.text


# --- Account lockout -------------------------------------------------------


async def wrong_password(client: AsyncClient):
    return await client.post(
        LOGIN, data={"username": "user@example.com", "password": "wrong"}
    )


async def test_too_many_wrong_passwords_lock_the_account(
    client: AsyncClient, regular_user: User, monkeypatch
):
    monkeypatch.setattr(settings, "MAX_FAILED_LOGIN_ATTEMPTS", 3)
    assert (await wrong_password(client)).status_code == 401
    assert (await wrong_password(client)).status_code == 401
    resp = await wrong_password(client)
    assert resp.status_code == 403
    assert "locked" in resp.json()["detail"]

    # The right password doesn't help any more.
    resp = await password_login(client)
    assert resp.status_code == 403


async def test_successful_login_resets_the_count(
    client: AsyncClient, regular_user: User, monkeypatch
):
    monkeypatch.setattr(settings, "MAX_FAILED_LOGIN_ATTEMPTS", 3)
    await wrong_password(client)
    await wrong_password(client)
    assert (await password_login(client)).status_code == 200
    await wrong_password(client)
    await wrong_password(client)
    assert (await password_login(client)).status_code == 200


async def test_lockout_can_be_turned_off(
    client: AsyncClient, regular_user: User, monkeypatch
):
    monkeypatch.setattr(settings, "MAX_FAILED_LOGIN_ATTEMPTS", 0)
    for _ in range(12):
        assert (await wrong_password(client)).status_code == 401
    assert (await password_login(client)).status_code == 200


async def test_admin_unlocks_account(
    superuser_client: AsyncClient,
    db_session: AsyncSession,
    regular_user: User,
    monkeypatch,
):
    monkeypatch.setattr(settings, "MAX_FAILED_LOGIN_ATTEMPTS", 1)
    await wrong_password(superuser_client)
    users = (await superuser_client.get("/api/v1/users")).json()
    assert next(u for u in users if u["id"] == str(regular_user.id))["is_locked"] is True

    resp = await superuser_client.post(f"/api/v1/users/{regular_user.id}/unlock")
    assert resp.status_code == 200, resp.text
    assert resp.json()["is_locked"] is False

    superuser_client.cookies.clear()
    assert (await password_login(superuser_client)).status_code == 200


async def test_unlock_needs_managing_users(auth_client: AsyncClient, regular_user: User):
    resp = await auth_client.post(f"/api/v1/users/{regular_user.id}/unlock")
    assert resp.status_code == 403
