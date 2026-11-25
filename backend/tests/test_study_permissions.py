"""Studies and their data can be viewed by anyone but edited only by
members of the owning laboratory - or by admins acting for a laboratory
(see test_admin_data_entry.py)."""

import pytest
import pytest_asyncio

from app.core.security import create_access_token
from app.models.laboratory import Laboratory, LaboratoryApprovalStatus
from app.models.study import Study
from app.models.user import User
from tests.conftest import _make_user


@pytest_asyncio.fixture
async def other_lab(db_session) -> Laboratory:
    lab = Laboratory(
        laboratory_name="Other Lab",
        institutional_affiliation="Other Institution",
        city="Elsewhere",
        country="Testland",
        approval_status=LaboratoryApprovalStatus.approved,
    )
    db_session.add(lab)
    await db_session.commit()
    await db_session.refresh(lab)
    return lab


async def _study(db_session, laboratory: Laboratory, published=True) -> Study:
    study = Study(title="A study", laboratory_id=laboratory.id, published=published)
    db_session.add(study)
    await db_session.commit()
    await db_session.refresh(study)
    return study


@pytest_asyncio.fixture
async def foreign_study(db_session, other_lab) -> Study:
    return await _study(db_session, other_lab)


@pytest_asyncio.fixture
async def own_study(db_session, laboratory) -> Study:
    return await _study(db_session, laboratory)


def _login(client, user: User):
    client.cookies.update({"access_token": create_access_token(subject=str(user.id))})
    return client


@pytest.mark.asyncio
async def test_lab_admin_can_view_but_not_edit_foreign_study(
    lab_admin_client, foreign_study
):
    response = await lab_admin_client.get(f"/api/v1/studies/{foreign_study.id}")
    assert response.status_code == 200

    response = await lab_admin_client.patch(
        f"/api/v1/studies/{foreign_study.id}", json={"title": "Hijacked"}
    )
    assert response.status_code == 403

    response = await lab_admin_client.delete(f"/api/v1/studies/{foreign_study.id}")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_regular_user_cannot_edit_foreign_study(auth_client, foreign_study):
    response = await auth_client.patch(
        f"/api/v1/studies/{foreign_study.id}", json={"title": "Hijacked"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_member_can_edit_own_study(auth_client, own_study):
    response = await auth_client.patch(
        f"/api/v1/studies/{own_study.id}", json={"title": "Renamed"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Renamed"


@pytest.mark.asyncio
async def test_regular_user_cannot_move_study_to_other_lab(
    auth_client, own_study, other_lab
):
    response = await auth_client.patch(
        f"/api/v1/studies/{own_study.id}", json={"laboratory_id": str(other_lab.id)}
    )
    assert response.status_code == 200
    assert response.json()["laboratory_id"] == str(own_study.laboratory_id)


@pytest.mark.asyncio
async def test_data_entrant_cannot_add_samples_to_foreign_study(
    client, data_entrant, foreign_study, own_study
):
    _login(client, data_entrant)
    response = await client.post(
        "/api/v1/samples", json={"study_id": str(foreign_study.id)}
    )
    assert response.status_code == 403

    response = await client.post(
        "/api/v1/samples", json={"study_id": str(own_study.id)}
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_member_without_data_entry_permission_cannot_add_samples(
    auth_client, own_study
):
    response = await auth_client.post(
        "/api/v1/samples", json={"study_id": str(own_study.id)}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_data_entrant_cannot_edit_results_of_foreign_study(
    client, db_session, other_lab, foreign_study, data_entrant, data_entry_group
):
    other_admin = await _make_user(
        db_session, other_lab, email="other@example.com", groups=[data_entry_group]
    )
    _login(client, other_admin)
    sample = (
        await client.post("/api/v1/samples", json={"study_id": str(foreign_study.id)})
    ).json()
    result = (
        await client.post("/api/v1/results", json={"sample_id": sample["id"]})
    ).json()

    _login(client, data_entrant)
    response = await client.patch(
        f"/api/v1/results/{result['id']}", json={"dna_concentration": 1.0}
    )
    assert response.status_code == 403
    response = await client.delete(f"/api/v1/samples/{sample['id']}")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_foreign_scenario_can_be_linked_but_not_edited(
    client, db_session, other_lab, foreign_study, own_study, data_entrant, data_entry_group
):
    other_admin = await _make_user(
        db_session, other_lab, email="other@example.com", groups=[data_entry_group]
    )
    _login(client, other_admin)
    category = (
        await client.post("/api/v1/scenario-categories", json={"name": "Cat"})
    ).json()
    scenario = (
        await client.post(
            "/api/v1/scenarios",
            json={
                "name": "Theirs",
                "realistic": True,
                "scenario_category_id": category["id"],
                "owning_study_id": str(foreign_study.id),
                "study_ids": [str(foreign_study.id)],
            },
        )
    ).json()

    _login(client, data_entrant)
    # Linking it into our own study is fine...
    response = await client.patch(
        f"/api/v1/scenarios/{scenario['id']}",
        json={"study_ids": [str(foreign_study.id), str(own_study.id)]},
    )
    assert response.status_code == 200
    # ...but editing it, or unlinking it from its own study, is not.
    response = await client.patch(
        f"/api/v1/scenarios/{scenario['id']}", json={"name": "Mine now"}
    )
    assert response.status_code == 403
    response = await client.patch(
        f"/api/v1/scenarios/{scenario['id']}", json={"study_ids": [str(own_study.id)]}
    )
    assert response.status_code == 403
    response = await client.delete(f"/api/v1/scenarios/{scenario['id']}")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_foreign_studys_item_can_be_used_in_own_surface_templates(
    client, db_session, other_lab, foreign_study, own_study, data_entrant, data_entry_group
):
    """Items are a shared catalog: referencing another lab's item in our own
    contact templates must not be blocked, but their surface templates stay
    theirs."""
    other_admin = await _make_user(
        db_session, other_lab, email="other@example.com", groups=[data_entry_group]
    )
    _login(client, other_admin)
    item = (
        await client.post(
            "/api/v1/items",
            json={"description": "Their mug", "study_ids": [str(foreign_study.id)]},
        )
    ).json()
    category = (
        await client.post("/api/v1/scenario-categories", json={"name": "Cat"})
    ).json()
    their_scenario = (
        await client.post(
            "/api/v1/scenarios",
            json={
                "name": "Theirs",
                "realistic": True,
                "scenario_category_id": category["id"],
                "owning_study_id": str(foreign_study.id),
                "study_ids": [str(foreign_study.id)],
            },
        )
    ).json()
    their_surface_template = (
        await client.post("/api/v1/surface-templates", json={"item_id": item["id"]})
    ).json()
    response = await client.post(
        "/api/v1/contact-templates",
        json={
            "donor_surface_template_id": their_surface_template["id"],
            "scenario_ids": [their_scenario["id"]],
        },
    )
    assert response.status_code == 201

    _login(client, data_entrant)
    # Building our own scenario around their item works...
    response = await client.post(
        "/api/v1/surface-templates", json={"item_id": item["id"]}
    )
    assert response.status_code == 201
    surface_template = response.json()
    response = await client.patch(
        f"/api/v1/surface-templates/{surface_template['id']}",
        json={"further_description_of_background_and_prevalence": "Mine"},
    )
    assert response.status_code == 200
    # ...but their surface templates can't be changed.
    response = await client.patch(
        f"/api/v1/surface-templates/{their_surface_template['id']}",
        json={"item_id": None},
    )
    assert response.status_code == 403
    response = await client.delete(
        f"/api/v1/surface-templates/{their_surface_template['id']}"
    )
    assert response.status_code == 403
