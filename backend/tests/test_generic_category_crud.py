"""
Many lookup/category routers (activity categories, sexes, dye sets, etc.)
are generated from the same CRUDBase + {name, description} pattern. Rather
than duplicating near-identical tests per router, this exercises that shared
behavior once across a representative sample of them.
"""

import pytest
from httpx import AsyncClient

CATEGORY_ENDPOINTS = [
    "/api/v1/activity-categories",
    "/api/v1/body-part-condition-categories",
    "/api/v1/inhibition-categories",
    "/api/v1/sexes",
    "/api/v1/experience-levels",
    "/api/v1/dye-sets",
    "/api/v1/disturbance-categories",
    "/api/v1/geographic-location-categories",
]


@pytest.mark.parametrize("endpoint", CATEGORY_ENDPOINTS)
async def test_list_is_empty_initially(client: AsyncClient, endpoint: str):
    resp = await client.get(endpoint)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.parametrize("endpoint", CATEGORY_ENDPOINTS)
async def test_anonymous_cannot_create(client: AsyncClient, endpoint: str):
    resp = await client.post(endpoint, json={"name": "Nope"})
    assert resp.status_code == 401


@pytest.mark.parametrize("endpoint", CATEGORY_ENDPOINTS)
async def test_regular_user_can_create_but_not_update(auth_client: AsyncClient, endpoint: str):
    create_resp = await auth_client.post(endpoint, json={"name": "Nope"})
    assert create_resp.status_code == 201
    obj_id = create_resp.json()["id"]

    update_resp = await auth_client.patch(f"{endpoint}/{obj_id}", json={"name": "Nope 2"})
    assert update_resp.status_code == 403

    delete_resp = await auth_client.delete(f"{endpoint}/{obj_id}")
    assert delete_resp.status_code == 403


@pytest.mark.parametrize("endpoint", CATEGORY_ENDPOINTS)
async def test_lab_admin_can_update_but_not_delete(lab_admin_client: AsyncClient, endpoint: str):
    create_resp = await lab_admin_client.post(endpoint, json={"name": "Example"})
    assert create_resp.status_code == 201
    obj_id = create_resp.json()["id"]

    update_resp = await lab_admin_client.patch(f"{endpoint}/{obj_id}", json={"name": "Updated"})
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Updated"

    delete_resp = await lab_admin_client.delete(f"{endpoint}/{obj_id}")
    assert delete_resp.status_code == 403


@pytest.mark.parametrize("endpoint", CATEGORY_ENDPOINTS)
async def test_superuser_crud_lifecycle(superuser_client: AsyncClient, endpoint: str):
    create_resp = await superuser_client.post(endpoint, json={"name": "Example"})
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["name"] == "Example"
    obj_id = created["id"]

    list_resp = await superuser_client.get(endpoint)
    assert list_resp.status_code == 200
    assert any(item["id"] == obj_id for item in list_resp.json())

    get_resp = await superuser_client.get(f"{endpoint}/{obj_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == obj_id

    update_resp = await superuser_client.patch(f"{endpoint}/{obj_id}", json={"name": "Updated"})
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Updated"

    delete_resp = await superuser_client.delete(f"{endpoint}/{obj_id}")
    assert delete_resp.status_code == 204

    missing_resp = await superuser_client.get(f"{endpoint}/{obj_id}")
    assert missing_resp.status_code == 204


@pytest.mark.parametrize("endpoint", CATEGORY_ENDPOINTS)
async def test_get_by_unknown_id_returns_no_content(
    superuser_client: AsyncClient, endpoint: str
):
    import uuid

    resp = await superuser_client.get(f"{endpoint}/{uuid.uuid4()}")
    assert resp.status_code == 204
