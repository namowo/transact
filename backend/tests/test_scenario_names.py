"""Scenario names are unique within a study (ignoring case and spacing),
since scenarios are picked by name, e.g. in the Excel planning sheet."""

import pytest
import pytest_asyncio

from app.models.scenario_category import ScenarioCategory
from app.models.study import Study


@pytest_asyncio.fixture
async def setup(db_session, laboratory):
    category = ScenarioCategory(name="Direct")
    first = Study(title="First", laboratory_id=laboratory.id)
    second = Study(title="Second", laboratory_id=laboratory.id)
    db_session.add_all([category, first, second])
    await db_session.commit()
    return category, first, second


async def _create(client, name, study, category):
    return await client.post(
        "/api/v1/scenarios",
        json={
            "name": name,
            "realistic": True,
            "scenario_category_id": str(category.id),
            "owning_study_id": str(study.id),
            "study_ids": [str(study.id)],
        },
    )


@pytest.mark.asyncio
async def test_duplicate_names_are_rejected(superuser_client, setup):
    category, first, second = setup
    response = await _create(superuser_client, "Handshake", first, category)
    assert response.status_code == 201, response.text
    handshake = response.json()["id"]

    response = await _create(superuser_client, "  handshake ", first, category)
    assert response.status_code == 409
    assert "already has a scenario named 'Handshake'" in response.json()["detail"]

    # Another study may use the same name.
    response = await _create(superuser_client, "Handshake", second, category)
    assert response.status_code == 201, response.text
    other_handshake = response.json()["id"]

    # Renaming into a taken name is rejected; renaming to a free one works,
    # and so does saving it under its own name.
    response = await _create(superuser_client, "Mug", first, category)
    mug = response.json()["id"]
    response = await superuser_client.patch(f"/api/v1/scenarios/{mug}", json={"name": "HANDSHAKE"})
    assert response.status_code == 409
    response = await superuser_client.patch(f"/api/v1/scenarios/{mug}", json={"name": "Cup"})
    assert response.status_code == 200, response.text
    response = await superuser_client.patch(f"/api/v1/scenarios/{handshake}", json={"name": "Handshake", "realistic": False})
    assert response.status_code == 200, response.text

    # Linking a scenario into a study that already has one by that name.
    response = await superuser_client.patch(
        f"/api/v1/scenarios/{other_handshake}",
        json={"study_ids": [str(second.id), str(first.id)]},
    )
    assert response.status_code == 409
