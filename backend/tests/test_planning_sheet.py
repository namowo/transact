"""The planning sheet round trip: download the .xlsx, fill in individuals
and items, upload it again."""

from io import BytesIO

import pytest
import pytest_asyncio
from openpyxl import load_workbook
from sqlalchemy import select

from app.models.individual import Individual
from app.models.item import Item
from app.models.item_category import ItemCategory
from app.models.item_subcategory import ItemSubcategory
from app.models.scenario import Scenario
from app.models.scenario_category import ScenarioCategory
from app.models.sex import Sex
from app.models.study import Study


@pytest_asyncio.fixture
async def study(db_session, laboratory) -> Study:
    category = ScenarioCategory(name="Direct")
    db_session.add(category)
    await db_session.flush()
    study = Study(title="Planning study", laboratory_id=laboratory.id, published=False)
    study.scenarios = [
        Scenario(name="Handshake", realistic=True, scenario_category_id=category.id),
        Scenario(name="Mug", realistic=True, scenario_category_id=category.id),
    ]
    db_session.add_all([
        study,
        Sex(name="female"),
        Sex(name="male"),
    ])
    cup = ItemCategory(name="Cup")
    db_session.add(cup)
    await db_session.flush()
    db_session.add(ItemSubcategory(name="Ceramic", item_category_id=cup.id))
    await db_session.commit()
    await db_session.refresh(study)
    return study


async def _download(client, study) -> bytes:
    response = await client.get(f"/api/v1/studies/{study.id}/planning-sheet")
    assert response.status_code == 200, response.text
    return response.content


def _fill(content: bytes, individuals=(), items=()) -> bytes:
    wb = load_workbook(BytesIO(content))
    for sheet, rows in (("Individuals", individuals), ("Items", items)):
        ws = wb[sheet]
        for row in rows:
            ws.append(list(row))
    out = BytesIO()
    wb.save(out)
    return out.getvalue()


async def _upload(client, study, content: bytes):
    return await client.post(
        f"/api/v1/studies/{study.id}/planning-sheet",
        content=content,
        headers={"Content-Type": "application/octet-stream"},
    )


@pytest.mark.asyncio
async def test_round_trip_creates_then_updates(superuser_client, db_session, study):
    sheet = _fill(
        await _download(superuser_client, study),
        individuals=[[None, "P01", "Female", 34, None, None, None, "Handshake; mug"]],
        items=[[None, "cup", "ceramic", "White mug", "Mug"]],
    )
    wb = load_workbook(BytesIO(sheet))
    assert wb.sheetnames[0] == "How to use"
    assert wb.active.title == "How to use"
    # Excel shows an empty dropdown when the list reference starts with "=".
    sex_dropdown = next(
        dv for dv in wb["Individuals"].data_validations.dataValidation if "C2" in str(dv.sqref)
    )
    assert sex_dropdown.formula1 == "'Lists'!$A$2:$A$3"
    assert [c.value for c in wb["Lists"]["A"][1:3]] == ["female", "male"]

    response = await _upload(superuser_client, study, sheet)
    assert response.status_code == 200, response.text
    assert response.json() == {
        "individuals_created": 1,
        "individuals_updated": 0,
        "items_created": 1,
        "items_updated": 0,
        "categories_created": 0,
        "subcategories_created": 0,
    }

    individual = (
        await db_session.execute(select(Individual).where(Individual.study_id == study.id))
    ).scalar_one()
    assert individual.age == 34
    assert individual.sex.name == "female"
    assert {s.name for s in individual.scenarios} == {"Handshake", "Mug"}
    item = (
        await db_session.execute(select(Item).where(Item.studies.any(Study.id == study.id)))
    ).scalar_one()
    assert item.item_subcategory.name == "Ceramic"

    # The next download lists them with their IDs; changing a row updates it.
    wb = load_workbook(BytesIO(await _download(superuser_client, study)))
    ws = wb["Individuals"]
    assert ws["A2"].value == str(individual.id)
    assert ws["H2"].value == "Handshake; Mug"
    ws["D2"] = 35
    out = BytesIO()
    wb.save(out)
    response = await _upload(superuser_client, study, out.getvalue())
    assert response.status_code == 200, response.text
    assert response.json()["individuals_updated"] == 1
    assert response.json()["individuals_created"] == 0
    await db_session.refresh(individual)
    assert individual.age == 35


@pytest.mark.asyncio
async def test_invalid_rows_reject_the_whole_file(superuser_client, db_session, study):
    sheet = _fill(
        await _download(superuser_client, study),
        individuals=[
            [None, "P01", "female", 30, None, None, None, "Handshake"],
            [None, "P02", "robot", 12.5, None, None, None, None],
        ],
        items=[[None, "Cup", "Glass", None, "Nowhere"]],
    )
    response = await _upload(superuser_client, study, sheet)
    assert response.status_code == 422
    errors = response.json()["detail"]["errors"]
    assert any("row 3" in e and "Sex 'robot'" in e for e in errors)
    assert any("row 3" in e and "Age" in e for e in errors)
    assert any("scenario 'Nowhere'" in e for e in errors)

    count = (
        await db_session.execute(select(Individual).where(Individual.study_id == study.id))
    ).scalars().all()
    assert count == []


@pytest.mark.asyncio
async def test_other_laboratories_cannot_upload(client, db_session, study):
    from app.models.laboratory import Laboratory, LaboratoryApprovalStatus
    from app.core.permission_catalog import Permission
    from tests.conftest import _make_user, make_group
    from app.core.security import create_access_token

    other = Laboratory(
        laboratory_name="Other",
        institutional_affiliation="Other",
        city="X",
        country="Y",
        approval_status=LaboratoryApprovalStatus.approved,
    )
    db_session.add(other)
    await db_session.commit()
    # Allowed to enter data - but for their own laboratory only.
    group = await make_group(db_session, "Data entry", [Permission.ENTER_DATA])
    outsider = await _make_user(db_session, other, email="out@example.com", groups=[group])
    client.cookies.update({"access_token": create_access_token(subject=str(outsider.id))})

    response = await _upload(client, study, b"irrelevant")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_new_categories_need_confirmation(superuser_client, db_session, study):
    sheet = _fill(
        await _download(superuser_client, study),
        items=[
            [None, "Cup", "Glass", "Wine glass", "Mug"],
            [None, "Door handle", "Brass", None, None],
            [None, "door  HANDLE", "brass", "Back door", None],
        ],
    )
    response = await _upload(superuser_client, study, sheet)
    assert response.status_code == 409, response.text
    detail = response.json()["detail"]
    # Spelled differently, still one new category / subcategory.
    assert detail["new_categories"] == ["Door handle"]
    assert detail["new_subcategories"] == [
        {"category": "Cup", "name": "Glass"},
        {"category": "Door handle", "name": "Brass"},
    ]
    # The two door handles have no scenario yet.
    assert detail["unassigned_items"] == 2
    assert (await db_session.execute(select(ItemCategory).where(ItemCategory.name == "Door handle"))).first() is None

    response = await superuser_client.post(
        f"/api/v1/studies/{study.id}/planning-sheet",
        params={"create_categories": "true", "scenario_ids": [str(study.scenarios[0].id)]},
        content=sheet,
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert (body["categories_created"], body["subcategories_created"], body["items_created"]) == (1, 2, 3)

    items = (
        await db_session.execute(select(Item).where(Item.studies.any(Study.id == study.id)))
    ).scalars().all()
    handles = [item for item in items if item.item_category.name == "Door handle"]
    assert len(handles) == 2
    assert {item.item_subcategory_id for item in handles} == {handles[0].item_subcategory_id}
    assert handles[0].item_subcategory.name == "Brass"


@pytest.mark.asyncio
async def test_rows_without_scenario_get_the_chosen_ones(superuser_client, db_session, study):
    handshake, mug = sorted(study.scenarios, key=lambda s: s.name)
    sheet = _fill(
        await _download(superuser_client, study),
        individuals=[
            [None, "P01", "female", 30, None, None, None, None],
            [None, "P02", "male", 40, None, None, None, "Mug"],
        ],
        items=[[None, "Cup", None, "Plain cup", None]],
    )
    response = await _upload(superuser_client, study, sheet)
    assert response.status_code == 409, response.text
    detail = response.json()["detail"]
    assert (detail["unassigned_individuals"], detail["unassigned_items"]) == (1, 1)
    assert detail["new_categories"] == []

    # Scenarios of another study can't be assigned.
    response = await superuser_client.post(
        f"/api/v1/studies/{study.id}/planning-sheet",
        params={"scenario_ids": ["00000000-0000-0000-0000-000000000000"]},
        content=sheet,
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 422

    response = await superuser_client.post(
        f"/api/v1/studies/{study.id}/planning-sheet",
        params={"scenario_ids": [str(handshake.id)]},
        content=sheet,
        headers={"Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 200, response.text

    individuals = {
        i.name: i
        for i in (
            await db_session.execute(select(Individual).where(Individual.study_id == study.id))
        ).scalars()
    }
    assert [s.name for s in individuals["P01"].scenarios] == ["Handshake"]
    # A row with its own scenario keeps it.
    assert [s.name for s in individuals["P02"].scenarios] == ["Mug"]
    item = (
        await db_session.execute(select(Item).where(Item.studies.any(Study.id == study.id)))
    ).scalar_one()
    assert [s.name for s in item.scenarios] == ["Handshake"]

    # Re-uploading with the Scenarios cell cleared keeps an existing row's scenarios.
    wb = load_workbook(BytesIO(await _download(superuser_client, study)))
    for row in wb["Individuals"].iter_rows(min_row=2, max_row=3):
        row[7].value = None
    out = BytesIO()
    wb.save(out)
    response = await _upload(superuser_client, study, out.getvalue())
    assert response.status_code == 200, response.text
    await db_session.refresh(individuals["P02"])
    assert [s.name for s in individuals["P02"].scenarios] == ["Mug"]
