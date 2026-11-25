"""Groups bundle permissions. Admins define platform-wide groups, lab admins
their laboratory's own groups, and nobody hands out permissions they don't
hold themselves."""

import pytest
import pytest_asyncio

from app.core.permission_catalog import ALL_PERMISSIONS, Permission, SystemGroup
from app.core.security import create_access_token
from app.crud.user_group import get_system_group
from app.models.laboratory import Laboratory
from app.models.user import User
from tests.conftest import _make_user, make_group


def _login(client, user: User):
    client.cookies.update({"access_token": create_access_token(subject=str(user.id))})
    return client


@pytest_asyncio.fixture
async def other_lab(db_session) -> Laboratory:
    lab = Laboratory(
        laboratory_name="Other Lab", institutional_affiliation="x", city="x", country="x"
    )
    db_session.add(lab)
    await db_session.commit()
    await db_session.refresh(lab)
    return lab


@pytest_asyncio.fixture
async def outsider(db_session, other_lab) -> User:
    return await _make_user(db_session, other_lab, email="outsider@example.com")


# --- Catalog and reading -------------------------------------------------------


@pytest.mark.asyncio
async def test_permissions_are_listed(client):
    response = await client.get("/api/v1/permissions")
    assert response.status_code == 200
    assert {p["key"] for p in response.json()} == {p.value for p in ALL_PERMISSIONS}


@pytest.mark.asyncio
async def test_me_reports_groups_and_permissions(lab_admin_client):
    me = (await lab_admin_client.get("/api/v1/users/me")).json()
    assert [g["system_key"] for g in me["groups"]] == [SystemGroup.LAB_ADMINISTRATOR.value]
    assert Permission.MANAGE_LAB_MEMBERS.value in me["permissions"]
    assert Permission.MANAGE_USERS.value not in me["permissions"]


@pytest.mark.asyncio
async def test_regular_user_cannot_list_groups(auth_client):
    response = await auth_client.get("/api/v1/user-groups")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_lab_admin_sees_global_and_own_lab_groups_only(
    lab_admin_client, db_session, laboratory, other_lab
):
    await make_group(db_session, "Ours", [Permission.ENTER_DATA], laboratory)
    await make_group(db_session, "Theirs", [Permission.ENTER_DATA], other_lab)
    names = {g["name"] for g in (await lab_admin_client.get("/api/v1/user-groups")).json()}
    assert "Ours" in names
    assert "Theirs" not in names
    assert "Administrator" in names


# --- Defining groups -----------------------------------------------------------


@pytest.mark.asyncio
async def test_admin_creates_global_group(superuser_client):
    response = await superuser_client.post(
        "/api/v1/user-groups",
        json={"name": "Data entry", "permissions": ["data.enter", "catalog.edit"]},
    )
    assert response.status_code == 201
    assert response.json()["laboratory_id"] is None
    assert response.json()["permissions"] == ["catalog.edit", "data.enter"]


@pytest.mark.asyncio
async def test_group_names_are_unique_per_scope(superuser_client, laboratory):
    await superuser_client.post("/api/v1/user-groups", json={"name": "Team"})
    response = await superuser_client.post("/api/v1/user-groups", json={"name": "team"})
    assert response.status_code == 400
    # The same name within a laboratory is fine.
    response = await superuser_client.post(
        "/api/v1/user-groups", json={"name": "Team", "laboratory_id": str(laboratory.id)}
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_lab_admin_cannot_create_global_group(lab_admin_client):
    response = await lab_admin_client.post("/api/v1/user-groups", json={"name": "Mine"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_lab_admin_creates_lab_group(lab_admin_client, laboratory):
    response = await lab_admin_client.post(
        "/api/v1/user-groups",
        json={
            "name": "Member managers",
            "permissions": ["lab.manage_members"],
            "laboratory_id": str(laboratory.id),
        },
    )
    assert response.status_code == 201
    assert response.json()["laboratory_id"] == str(laboratory.id)


@pytest.mark.asyncio
async def test_lab_group_cannot_hold_global_permissions(superuser_client, laboratory):
    response = await superuser_client.post(
        "/api/v1/user-groups",
        json={
            "name": "Too much",
            "permissions": ["users.manage"],
            "laboratory_id": str(laboratory.id),
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_lab_admin_cannot_create_groups_for_other_labs(lab_admin_client, other_lab):
    response = await lab_admin_client.post(
        "/api/v1/user-groups",
        json={"name": "Theirs", "laboratory_id": str(other_lab.id)},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_cannot_grant_permissions_one_lacks(lab_admin_client, laboratory):
    # Lab administrators don't enter data by default, so they can't hand it out.
    response = await lab_admin_client.post(
        "/api/v1/user-groups",
        json={
            "name": "Data entry",
            "permissions": ["data.enter"],
            "laboratory_id": str(laboratory.id),
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_lab_admin_cannot_edit_global_groups(lab_admin_client, db_session):
    group = await get_system_group(db_session, SystemGroup.QUALITY_CHECKER)
    response = await lab_admin_client.patch(
        f"/api/v1/user-groups/{group.id}", json={"permissions": []}
    )
    assert response.status_code == 403


# --- Built-in groups -----------------------------------------------------------


@pytest.mark.asyncio
async def test_administrator_group_keeps_its_core_permissions(
    superuser_client, db_session
):
    group = await get_system_group(db_session, SystemGroup.ADMINISTRATOR)
    response = await superuser_client.patch(
        f"/api/v1/user-groups/{group.id}", json={"permissions": ["data.enter"]}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_built_in_groups_cannot_be_deleted_or_renamed(superuser_client, db_session):
    group = await get_system_group(db_session, SystemGroup.QUALITY_CHECKER)
    response = await superuser_client.delete(f"/api/v1/user-groups/{group.id}")
    assert response.status_code == 400
    response = await superuser_client.patch(
        f"/api/v1/user-groups/{group.id}", json={"name": "Reviewers"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_custom_group_can_be_deleted(superuser_client):
    group = (
        await superuser_client.post("/api/v1/user-groups", json={"name": "Temp"})
    ).json()
    response = await superuser_client.delete(f"/api/v1/user-groups/{group['id']}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_last_administrator_cannot_leave(superuser_client, superuser):
    response = await superuser_client.put(
        f"/api/v1/users/{superuser.id}/groups", json={"group_ids": []}
    )
    assert response.status_code == 400


# --- Assigning groups ----------------------------------------------------------


@pytest.mark.asyncio
async def test_admin_assigns_any_group(superuser_client, db_session, regular_user):
    group = await get_system_group(db_session, SystemGroup.QUALITY_CHECKER)
    response = await superuser_client.put(
        f"/api/v1/users/{regular_user.id}/groups", json={"group_ids": [str(group.id)]}
    )
    assert response.status_code == 200
    assert Permission.QUALITY_CHECK.value in response.json()["permissions"]


@pytest.mark.asyncio
async def test_admin_can_make_another_admin(superuser_client, db_session, regular_user):
    group = await get_system_group(db_session, SystemGroup.ADMINISTRATOR)
    response = await superuser_client.put(
        f"/api/v1/users/{regular_user.id}/groups", json={"group_ids": [str(group.id)]}
    )
    assert response.status_code == 200
    assert Permission.MANAGE_USERS.value in response.json()["permissions"]


@pytest.mark.asyncio
async def test_lab_admin_assigns_own_lab_group(
    lab_admin_client, db_session, laboratory, regular_user
):
    group = await make_group(db_session, "Members", [Permission.MANAGE_LAB_MEMBERS], laboratory)
    response = await lab_admin_client.put(
        f"/api/v1/users/{regular_user.id}/groups", json={"group_ids": [str(group.id)]}
    )
    assert response.status_code == 200
    assert [g["name"] for g in response.json()["groups"]] == ["Members"]


@pytest.mark.asyncio
async def test_lab_admin_cannot_escalate(lab_admin_client, db_session, regular_user):
    for key in (SystemGroup.ADMINISTRATOR, SystemGroup.QUALITY_CHECKER):
        group = await get_system_group(db_session, key)
        response = await lab_admin_client.put(
            f"/api/v1/users/{regular_user.id}/groups", json={"group_ids": [str(group.id)]}
        )
        assert response.status_code == 403, key


@pytest.mark.asyncio
async def test_lab_admin_cannot_touch_other_labs_members(
    lab_admin_client, db_session, outsider
):
    group = await get_system_group(db_session, SystemGroup.LAB_ADMINISTRATOR)
    response = await lab_admin_client.put(
        f"/api/v1/users/{outsider.id}/groups", json={"group_ids": [str(group.id)]}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_lab_group_only_for_its_members(
    superuser_client, db_session, laboratory, outsider
):
    group = await make_group(db_session, "Ours", [Permission.ENTER_DATA], laboratory)
    response = await superuser_client.put(
        f"/api/v1/users/{outsider.id}/groups", json={"group_ids": [str(group.id)]}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_leaving_the_lab_drops_lab_groups(
    superuser_client, db_session, laboratory, other_lab
):
    lab_group = await make_group(db_session, "Ours", [Permission.ENTER_DATA], laboratory)
    member = await _make_user(
        db_session,
        laboratory,
        email="leaver@example.com",
        groups=[lab_group, SystemGroup.LAB_ADMINISTRATOR, SystemGroup.QUALITY_CHECKER],
    )
    response = await superuser_client.post(
        f"/api/v1/users/{member.id}/set-laboratory",
        json={"laboratory_id": str(other_lab.id)},
    )
    assert response.status_code == 200
    assert [g["system_key"] for g in response.json()["groups"]] == [
        SystemGroup.QUALITY_CHECKER.value
    ]


@pytest.mark.asyncio
async def test_new_member_gets_permissions_of_assigned_group(
    client, db_session, laboratory, regular_user, data_entry_group, superuser
):
    study = (
        await _login(client, regular_user).post(
            "/api/v1/studies", json={"title": "S", "laboratory_id": str(laboratory.id)}
        )
    ).json()
    response = await client.post("/api/v1/samples", json={"study_id": study["id"]})
    assert response.status_code == 403

    _login(client, superuser)
    await client.put(
        f"/api/v1/users/{regular_user.id}/groups",
        json={"group_ids": [str(data_entry_group.id)]},
    )

    _login(client, regular_user)
    response = await client.post("/api/v1/samples", json={"study_id": study["id"]})
    assert response.status_code == 201


# --- Joining laboratories ------------------------------------------------------


@pytest.mark.asyncio
async def test_users_cannot_move_themselves_into_a_lab(auth_client, other_lab):
    response = await auth_client.patch(
        "/api/v1/users/me", json={"laboratory_id": str(other_lab.id)}
    )
    assert response.status_code == 200
    assert response.json()["laboratory_id"] != str(other_lab.id)


@pytest.mark.asyncio
async def test_registration_ignores_laboratory(client, laboratory):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@example.com",
            "password": "Passw0rd!",
            "first_name": "New",
            "last_name": "User",
            "laboratory_id": str(laboratory.id),
        },
    )
    assert response.status_code == 201
    assert response.json()["laboratory_id"] is None


@pytest.mark.asyncio
async def test_founder_of_approved_lab_becomes_its_lab_admin(
    client, db_session, superuser
):
    founder = await _make_user(db_session, None, email="founder@example.com")
    _login(client, founder)
    request = (
        await client.post(
            "/api/v1/lab-membership-requests/new-laboratory",
            json={
                "laboratory_name": "Brand New",
                "institutional_affiliation": "x",
                "city": "x",
                "country": "x",
            },
        )
    ).json()

    _login(client, founder)
    response = await client.post(f"/api/v1/lab-membership-requests/{request['id']}/approve")
    assert response.status_code == 403

    _login(client, superuser)
    response = await client.post(f"/api/v1/lab-membership-requests/{request['id']}/approve")
    assert response.status_code == 200

    me = (await _login(client, founder).get("/api/v1/users/me")).json()
    assert me["laboratory_id"] == request["laboratory_id"]
    assert [g["system_key"] for g in me["groups"]] == [SystemGroup.LAB_ADMINISTRATOR.value]


@pytest.mark.asyncio
async def test_user_manager_outside_administrator_group_can_delete_users(
    client, db_session, laboratory, regular_user
):
    """The last-administrator guard only protects administrators."""
    managers = await make_group(db_session, "User managers", [Permission.MANAGE_USERS])
    manager = await _make_user(
        db_session, laboratory, email="manager@example.com", groups=[managers]
    )
    _login(client, manager)
    response = await client.delete(f"/api/v1/users/{regular_user.id}")
    assert response.status_code == 204
