"""Lab admins can replace the default planning checklist with their own."""

from io import BytesIO

import pytest
import pytest_asyncio
from openpyxl import load_workbook

from app.core.security import create_access_token
from app.models.laboratory import Laboratory, LaboratoryApprovalStatus
from app.models.study import Study
from app.services.planning_checklist import DEFAULT_SECTIONS
from app.core.permission_catalog import SystemGroup
from tests.conftest import _make_user

CUSTOM = [
    {
        "title": "Before the experiment",
        "items": [{"id": "book", "text": "Book the lab"}, {"text": "  "}, {"text": "Order swabs"}],
    }
]


@pytest_asyncio.fixture
async def study(db_session, laboratory) -> Study:
    study = Study(title="Checklist study", laboratory_id=laboratory.id, published=False)
    db_session.add(study)
    await db_session.commit()
    await db_session.refresh(study)
    return study


def _login(client, user):
    client.cookies.update({"access_token": create_access_token(subject=str(user.id))})
    return client


@pytest.mark.asyncio
async def test_default_until_a_lab_admin_saves_one(lab_admin_client, study, laboratory):
    url = f"/api/v1/studies/{study.id}/planning-checklist"
    response = await lab_admin_client.get(url)
    assert response.status_code == 200
    body = response.json()
    assert body["is_default"] is True
    assert body["can_edit"] is True
    assert body["sections"] == DEFAULT_SECTIONS

    response = await lab_admin_client.put(
        f"/api/v1/laboratories/{laboratory.id}/planning-checklist", json={"sections": CUSTOM}
    )
    assert response.status_code == 200, response.text
    # Blank items are dropped; new items get an id.
    items = response.json()["sections"][0]["items"]
    assert [item["text"] for item in items] == ["Book the lab", "Order swabs"]
    assert items[0]["id"] == "book"
    assert items[1]["id"]

    body = (await lab_admin_client.get(url)).json()
    assert body["is_default"] is False
    assert body["sections"][0]["title"] == "Before the experiment"

    # The Excel planning sheet uses the laboratory's checklist too.
    sheet = await lab_admin_client.get(f"/api/v1/studies/{study.id}/planning-sheet")
    values = [c.value for c in load_workbook(BytesIO(sheet.content))["Checklist"]["A"]]
    assert "Before the experiment" in values
    assert "Ethics" not in values

    response = await lab_admin_client.delete(f"/api/v1/laboratories/{laboratory.id}/planning-checklist")
    assert response.status_code == 200
    assert response.json()["is_default"] is True
    assert (await lab_admin_client.get(url)).json()["sections"] == DEFAULT_SECTIONS


@pytest.mark.asyncio
async def test_only_own_lab_admins_can_edit(client, db_session, study, laboratory, regular_user):
    _login(client, regular_user)
    assert (await client.get(f"/api/v1/studies/{study.id}/planning-checklist")).json()["can_edit"] is False
    response = await client.put(
        f"/api/v1/laboratories/{laboratory.id}/planning-checklist", json={"sections": CUSTOM}
    )
    assert response.status_code == 403

    other = Laboratory(
        laboratory_name="Other",
        institutional_affiliation="Other",
        city="X",
        country="Y",
        approval_status=LaboratoryApprovalStatus.approved,
    )
    db_session.add(other)
    await db_session.commit()
    other_admin = await _make_user(
        db_session, other, email="otheradmin@example.com",
        groups=[SystemGroup.LAB_ADMINISTRATOR],
    )
    _login(client, other_admin)
    response = await client.put(
        f"/api/v1/laboratories/{laboratory.id}/planning-checklist", json={"sections": CUSTOM}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_sections_need_a_title(lab_admin_client, laboratory):
    response = await lab_admin_client.put(
        f"/api/v1/laboratories/{laboratory.id}/planning-checklist",
        json={"sections": [{"title": "  ", "items": [{"text": "x"}]}]},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_lab_members_tick_items_off(client, db_session, study, regular_user):
    _login(client, regular_user)
    url = f"/api/v1/studies/{study.id}/planning-checklist"
    body = (await client.get(url)).json()
    assert body["can_check"] is True
    assert body["checked"] == []

    response = await client.put(
        f"{url}/progress",
        json={
            "checked": ["ethics-approval", "ethics-approval", "not-an-item"],
            "notes": {"ethics-approval": " Approved 2026-11-01 ", "ethics-consent": "  "},
        },
    )
    assert response.status_code == 200, response.text
    # Duplicates, unknown items and blank notes are dropped.
    assert response.json() == {
        "checked": ["ethics-approval"],
        "notes": {"ethics-approval": "Approved 2026-11-01"},
    }
    body = (await client.get(url)).json()
    assert body["checked"] == ["ethics-approval"]

    # The Excel sheet shows the ticks and notes.
    sheet = await client.get(f"/api/v1/studies/{study.id}/planning-sheet")
    ws = load_workbook(BytesIO(sheet.content))["Checklist"]
    row = next(r for r in ws.iter_rows(values_only=True) if r[0] == DEFAULT_SECTIONS[0]["items"][0]["text"])
    assert row[1:3] == ("Yes", "Approved 2026-11-01")


@pytest.mark.asyncio
async def test_other_laboratories_cannot_tick(client, db_session, study):
    other = Laboratory(
        laboratory_name="Other",
        institutional_affiliation="Other",
        city="X",
        country="Y",
        approval_status=LaboratoryApprovalStatus.approved,
    )
    db_session.add(other)
    await db_session.commit()
    outsider = await _make_user(db_session, other, email="outsider@example.com")
    _login(client, outsider)
    study.published = True
    await db_session.commit()
    url = f"/api/v1/studies/{study.id}/planning-checklist"
    assert (await client.get(url)).json()["can_check"] is False
    response = await client.put(f"{url}/progress", json={"checked": ["ethics-approval"]})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_download_is_named_after_the_study(lab_admin_client, db_session, study):
    study.title = "Übertragung Hände"
    await db_session.commit()
    response = await lab_admin_client.get(f"/api/v1/studies/{study.id}/planning-sheet")
    disposition = response.headers["content-disposition"]
    assert 'filename="transact-bertragung-h-nde-planning-checklist-' in disposition
    assert "filename*=UTF-8''transact-%C3%9Cbertragung_H%C3%A4nde_planning_checklist-" in disposition
