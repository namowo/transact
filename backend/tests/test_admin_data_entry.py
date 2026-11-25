"""Admins with "Edit data of all laboratories" can create a laboratory and
prepare its studies and data - until the laboratory switches that off, or
the permission is taken away from their group."""

import pytest
import pytest_asyncio

from app.core.permission_catalog import Permission, SystemGroup
from app.core.security import create_access_token
from app.crud.user_group import get_system_group
from app.models.laboratory import Laboratory
from app.models.study import Study
from app.models.user import User
from tests.conftest import _make_user

LAB = {
    "laboratory_name": "Prepared Lab",
    "institutional_affiliation": "Somewhere",
    "city": "Town",
    "country": "Land",
}


def _login(client, user: User):
    client.cookies.update({"access_token": create_access_token(subject=str(user.id))})
    return client


@pytest_asyncio.fixture
async def prepared_lab(db_session) -> Laboratory:
    lab = Laboratory(**LAB)
    db_session.add(lab)
    await db_session.commit()
    await db_session.refresh(lab)
    return lab


@pytest_asyncio.fixture
async def prepared_study(db_session, prepared_lab) -> Study:
    study = Study(title="Prepared", laboratory_id=prepared_lab.id, published=False)
    db_session.add(study)
    await db_session.commit()
    await db_session.refresh(study)
    return study


@pytest_asyncio.fixture
async def prepared_lab_admin(db_session, prepared_lab) -> User:
    return await _make_user(
        db_session,
        prepared_lab,
        email="takeover@example.com",
        groups=[SystemGroup.LAB_ADMINISTRATOR],
    )


@pytest.mark.asyncio
async def test_admin_creates_laboratory_and_prepares_its_data(superuser_client):
    response = await superuser_client.post("/api/v1/laboratories", json=LAB)
    assert response.status_code == 201
    lab = response.json()
    assert lab["allow_admin_data_entry"] is True

    response = await superuser_client.post(
        "/api/v1/studies", json={"title": "For them", "laboratory_id": lab["id"]}
    )
    assert response.status_code == 201
    study = response.json()
    assert study["laboratory_id"] == lab["id"]

    response = await superuser_client.patch(
        f"/api/v1/studies/{study['id']}", json={"title": "Renamed"}
    )
    assert response.status_code == 200

    response = await superuser_client.post(
        "/api/v1/samples", json={"study_id": study["id"]}
    )
    assert response.status_code == 201
    sample = response.json()
    response = await superuser_client.post(
        "/api/v1/results", json={"sample_id": sample["id"]}
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_regular_user_cannot_create_study_for_other_lab(auth_client, prepared_lab):
    response = await auth_client.post(
        "/api/v1/studies", json={"title": "Sneaky", "laboratory_id": str(prepared_lab.id)}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_laboratory_can_switch_admin_data_entry_off(
    client, superuser, prepared_lab, prepared_study, prepared_lab_admin
):
    _login(client, prepared_lab_admin)
    response = await client.put(
        f"/api/v1/laboratories/{prepared_lab.id}/data-access",
        json={"allow_admin_data_entry": False},
    )
    assert response.status_code == 200
    assert response.json()["allow_admin_data_entry"] is False

    _login(client, superuser)
    response = await client.patch(
        f"/api/v1/studies/{prepared_study.id}", json={"title": "Not anymore"}
    )
    assert response.status_code == 403
    response = await client.post(
        "/api/v1/samples", json={"study_id": str(prepared_study.id)}
    )
    assert response.status_code == 403
    response = await client.post(
        "/api/v1/studies", json={"title": "x", "laboratory_id": str(prepared_lab.id)}
    )
    assert response.status_code == 403

    # The laboratory's own admin isn't affected (data entry aside, which
    # needs its own permission).
    _login(client, prepared_lab_admin)
    response = await client.patch(
        f"/api/v1/studies/{prepared_study.id}", json={"title": "Ours"}
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_only_the_laboratory_decides_on_admin_data_entry(
    client, superuser, lab_admin, prepared_lab
):
    # Neither a platform admin from another lab...
    _login(client, superuser)
    response = await client.put(
        f"/api/v1/laboratories/{prepared_lab.id}/data-access",
        json={"allow_admin_data_entry": False},
    )
    assert response.status_code == 403
    # ...nor another laboratory's admin.
    _login(client, lab_admin)
    response = await client.put(
        f"/api/v1/laboratories/{prepared_lab.id}/data-access",
        json={"allow_admin_data_entry": False},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_removing_the_permission_from_the_group_disables_it(
    superuser_client, db_session, prepared_study
):
    admin_group = await get_system_group(db_session, SystemGroup.ADMINISTRATOR)
    remaining = [
        p for p in admin_group.permissions if p != Permission.EDIT_ALL_LABORATORY_DATA.value
    ]
    response = await superuser_client.patch(
        f"/api/v1/user-groups/{admin_group.id}", json={"permissions": remaining}
    )
    assert response.status_code == 200

    response = await superuser_client.patch(
        f"/api/v1/studies/{prepared_study.id}", json={"title": "Nope"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_laboratory_manager_can_move_study_to_another_lab(
    superuser_client, prepared_lab, laboratory, db_session
):
    study = Study(title="Mine", laboratory_id=laboratory.id)
    db_session.add(study)
    await db_session.commit()
    response = await superuser_client.patch(
        f"/api/v1/studies/{study.id}", json={"laboratory_id": str(prepared_lab.id)}
    )
    assert response.status_code == 200
    assert response.json()["laboratory_id"] == str(prepared_lab.id)
