"""Data download: which studies a download draws from, cross-study
filtering, definition validation, saved models and the file formats."""

import csv
import io
from datetime import timedelta

import pytest
import pytest_asyncio
from openpyxl import load_workbook

from app.core.security import create_access_token
from app.models.condition_during_contact import ConditionDuringContact
from app.models.contact import Contact
from app.models.contact_template import ContactTemplate
from app.models.geographic_location_category import GeographicLocationCategory
from app.models.individual import Individual
from app.models.item import Item
from app.models.item_category import ItemCategory
from app.models.laboratory import Laboratory, LaboratoryApprovalStatus
from app.models.pcr import PCR
from app.models.pcr_contributor import PCRContributor
from app.models.result import Result
from app.models.sample import Sample
from app.models.scenario import Scenario
from app.models.scenario_category import ScenarioCategory
from app.models.study import Study
from app.models.surface import Surface
from app.models.surface_template import SurfaceTemplate
from app.models.user import User
from app.services.data_export.fields import DATASETS
from app.services.data_export.presets import PRESETS
from app.services.data_export.query import validate_definition
from tests.conftest import _make_user

API = "/api/v1/data-models"


def _login(client, user: User):
    client.cookies.update({"access_token": create_access_token(subject=str(user.id))})
    return client


@pytest_asyncio.fixture
async def other_lab(db_session) -> Laboratory:
    lab = Laboratory(
        laboratory_name="Other Lab",
        institutional_affiliation="Other Institution",
        city="Elsewhere",
        country="Otherland",
        approval_status=LaboratoryApprovalStatus.approved,
    )
    db_session.add(lab)
    await db_session.commit()
    return lab


@pytest_asyncio.fixture
async def categories(db_session):
    handling = ScenarioCategory(name="Handling")
    wearing = ScenarioCategory(name="Wearing")
    knife = ItemCategory(name="Knife")
    db_session.add_all([handling, wearing, knife])
    await db_session.commit()
    return {"handling": handling, "wearing": wearing, "knife": knife}


async def _seed_study(
    db,
    *,
    lab: Laboratory,
    title: str,
    published: bool,
    qc: bool,
    category: ScenarioCategory,
    item_category: ItemCategory,
    concentration: float,
    contact_template: ContactTemplate | None = None,
    contact_duration: timedelta | None = None,
):
    """A study with one scenario, one contact (individual's hand -> item)
    and one sample with one result."""
    study = Study(
        title=title,
        laboratory_id=lab.id,
        published=published,
        quality_check_passed=qc,
        year="2025",
        doi=f"10.1/{title}",
    )
    db.add(study)
    await db.flush()

    item = Item(item_category_id=item_category.id, description=f"{title} knife")
    hand = SurfaceTemplate()
    blade = SurfaceTemplate()
    db.add_all([item, hand, blade])
    await db.flush()
    blade.item_id = item.id

    if contact_template is None:
        contact_template = ContactTemplate(
            name=f"{title} grip",
            duration=timedelta(seconds=10),
            donor_surface_template_id=hand.id,
            recipient_surface_template_id=blade.id,
        )
        db.add(contact_template)
        await db.flush()

    scenario = Scenario(
        name=f"{title} scenario",
        realistic=True,
        scenario_category_id=category.id,
        owning_study_id=study.id,
    )
    scenario.studies.append(study)
    scenario.contact_templates.append(contact_template)
    db.add(scenario)

    person = Individual(study_id=study.id, name=f"{title} person", age=30)
    db.add(person)
    await db.flush()

    donor = Surface(surface_template_id=hand.id, individual_id=person.id)
    recipient = Surface(surface_template_id=blade.id)
    db.add_all([donor, recipient])
    await db.flush()

    location = GeographicLocationCategory(name=f"{title} region")
    db.add(location)
    await db.flush()
    condition = ConditionDuringContact(temperature=21.0, geographic_location_category_id=location.id)
    db.add(condition)
    await db.flush()

    contact = Contact(
        contact_template_id=contact_template.id,
        donor_surface_id=donor.id,
        recipient_surface_id=recipient.id,
        duration=contact_duration,
        condition_during_contact_id=condition.id,
    )
    db.add(contact)
    await db.flush()

    sample = Sample(
        name=f"{title} sample",
        study_id=study.id,
        contact_id=contact.id,
        surface_id=recipient.id,
    )
    db.add(sample)
    await db.flush()
    result = Result(sample_id=sample.id, dna_concentration=concentration)
    db.add(result)
    await db.flush()
    pcr = PCR(result_id=result.id, no_of_contributors=2, average_rfu=500.5)
    db.add(pcr)
    await db.flush()
    db.add_all(
        [
            PCRContributor(pcr_id=pcr.id, individual_id=person.id, mixture_proportion=0.7),
            PCRContributor(pcr_id=pcr.id, unknown_label="UP1", mixture_proportion=0.3),
        ]
    )
    await db.commit()
    return study, contact_template


@pytest_asyncio.fixture
async def studies(db_session, laboratory, other_lab, categories):
    """
    public_a   own lab,   published + QC   -> everyone
    public_b   other lab, published + QC   -> everyone (shares A's contact template)
    unchecked  other lab, published, no QC -> nobody but other lab
    own_draft  own lab,   unpublished      -> own lab only
    foreign    other lab, unpublished      -> other lab only
    """
    c = categories
    public_a, template = await _seed_study(
        db_session, lab=laboratory, title="public_a", published=True, qc=True,
        category=c["handling"], item_category=c["knife"], concentration=1.5,
    )
    public_b, _ = await _seed_study(
        db_session, lab=other_lab, title="public_b", published=True, qc=True,
        category=c["handling"], item_category=c["knife"], concentration=2.5,
        contact_template=template, contact_duration=timedelta(seconds=30),
    )
    unchecked, _ = await _seed_study(
        db_session, lab=other_lab, title="unchecked", published=True, qc=False,
        category=c["handling"], item_category=c["knife"], concentration=3.5,
    )
    own_draft, _ = await _seed_study(
        db_session, lab=laboratory, title="own_draft", published=False, qc=False,
        category=c["wearing"], item_category=c["knife"], concentration=4.5,
    )
    foreign, _ = await _seed_study(
        db_session, lab=other_lab, title="foreign", published=False, qc=False,
        category=c["wearing"], item_category=c["knife"], concentration=5.5,
    )
    return dict(
        public_a=public_a, public_b=public_b, unchecked=unchecked,
        own_draft=own_draft, foreign=foreign,
    )


def _definition(**overrides):
    return {
        "dataset": "results",
        "columns": ["study.title", "scenario.name", "contact.duration", "result.dna_concentration"],
        **overrides,
    }


async def _titles(client, **overrides) -> list[str]:
    response = await client.post(f"{API}/preview", json=_definition(**overrides))
    assert response.status_code == 200, response.text
    return sorted(row[0] for row in response.json()["rows"])


# --- Which studies a download draws from -----------------------------------------


@pytest.mark.asyncio
async def test_guest_gets_only_published_and_quality_checked_studies(client, studies):
    assert await _titles(client) == ["public_a", "public_b"]


@pytest.mark.asyncio
async def test_member_also_gets_own_lab_unpublished_studies(client, studies, regular_user):
    _login(client, regular_user)
    # Never another lab's unpublished or unchecked data.
    assert await _titles(client) == ["own_draft", "public_a", "public_b"]


@pytest.mark.asyncio
async def test_superuser_gets_no_extra_studies(client, studies, superuser):
    _login(client, superuser)
    assert "foreign" not in await _titles(client)
    assert "unchecked" not in await _titles(client)


@pytest.mark.asyncio
async def test_study_scope_cannot_widen_visibility(client, studies):
    ids = [str(studies["foreign"].id), str(studies["public_a"].id)]
    assert await _titles(client, study_ids=ids) == ["public_a"]


@pytest.mark.asyncio
async def test_preview_counts_rows_and_studies(client, studies):
    response = await client.post(f"{API}/preview", json=_definition())
    body = response.json()
    assert body["total_rows"] == 2
    assert body["study_count"] == 2
    assert [c["key"] for c in body["columns"]] == _definition()["columns"]


@pytest.mark.asyncio
async def test_downloadable_studies_follow_visibility(client, studies, regular_user):
    guest = sorted(s["title"] for s in (await client.get(f"{API}/studies")).json())
    assert guest == ["public_a", "public_b"]
    _login(client, regular_user)
    member = {s["title"]: s["published"] for s in (await client.get(f"{API}/studies")).json()}
    assert member == {"public_a": True, "public_b": True, "own_draft": False}


@pytest.mark.asyncio
async def test_downloadable_studies_include_overview(client, studies):
    by_title = {s["title"]: s for s in (await client.get(f"{API}/studies")).json()}
    study = by_title["public_a"]
    assert study["scenario_count"] == 1
    assert study["sample_count"] == 1
    assert study["laboratory_name"]
    assert isinstance(study["authors"], list)


# --- Filtering across studies -----------------------------------------------------


@pytest.mark.asyncio
async def test_category_filter_returns_rows_from_several_studies(client, studies, regular_user):
    _login(client, regular_user)
    titles = await _titles(
        client, filters=[{"field": "scenario.category", "op": "in", "value": ["Handling"]}]
    )
    assert titles == ["public_a", "public_b"]


@pytest.mark.asyncio
async def test_numeric_filters(client, studies):
    gt = [{"field": "result.dna_concentration", "op": "gt", "value": 2}]
    assert await _titles(client, filters=gt) == ["public_b"]
    between = [{"field": "result.dna_concentration", "op": "between", "value": [1, 2]}]
    assert await _titles(client, filters=between) == ["public_a"]


@pytest.mark.asyncio
async def test_contains_filter_escapes_wildcards(client, studies):
    flt = [{"field": "study.title", "op": "contains", "value": "%"}]
    assert await _titles(client, filters=flt) == []
    flt = [{"field": "study.title", "op": "contains", "value": "LIC_B"}]
    assert await _titles(client, filters=flt) == ["public_b"]


@pytest.mark.asyncio
async def test_shared_template_does_not_duplicate_rows_or_leak_scenarios(client, studies):
    response = await client.post(f"{API}/preview", json=_definition())
    rows = {row[0]: row for row in response.json()["rows"]}
    assert len(response.json()["rows"]) == 2
    # The template is used by both studies' scenarios; each row only names
    # its own study's scenario.
    assert rows["public_a"][1] == "public_a scenario"
    assert rows["public_b"][1] == "public_b scenario"


@pytest.mark.asyncio
@pytest.mark.parametrize("dataset_key", list(DATASETS))
async def test_every_field_runs_and_stays_on_its_row(client, studies, regular_user, dataset_key):
    """Selecting every field at once must work and return one row per
    record. A subquery that fails to correlate with its row would either
    return several rows (an error) or values from other studies."""
    _login(client, regular_user)
    dataset = DATASETS[dataset_key]
    columns = [f.key for f in dataset.fields]
    response = await client.post(
        f"{API}/preview", json={"dataset": dataset_key, "columns": columns}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    for row in body["rows"]:
        values = dict(zip(columns, row))
        title = values["study.title"]
        for key, value in values.items():
            # Every study's names are prefixed with its title; a value
            # naming another study leaked across rows.
            if isinstance(value, str):
                for other in ("public_a", "public_b", "own_draft"):
                    if other != title and other in value:
                        # The shared contact template is public_a's.
                        assert key in ("contact.name", "contact.template"), (key, value)


@pytest.mark.asyncio
async def test_contact_conditions_resolve_per_row(client, studies):
    response = await client.post(
        f"{API}/preview",
        json=_definition(columns=["study.title", "contact_condition.geographic_location"]),
    )
    rows = dict(response.json()["rows"])
    assert rows == {"public_a": "public_a region", "public_b": "public_b region"}


@pytest.mark.asyncio
async def test_contributors_dataset(client, studies):
    response = await client.post(
        f"{API}/preview",
        json={
            "dataset": "pcr_contributors",
            "columns": ["study.title", "contributor.label", "contributor.known", "contributor.mixture_proportion"],
            "filters": [{"field": "contributor.known", "op": "eq", "value": True}],
        },
    )
    assert sorted(map(tuple, response.json()["rows"])) == [
        ("public_a", "public_a person", True, 0.7),
        ("public_b", "public_b person", True, 0.7),
    ]


@pytest.mark.asyncio
async def test_contact_values_fall_back_to_template(client, studies):
    response = await client.post(f"{API}/preview", json=_definition())
    rows = {row[0]: row for row in response.json()["rows"]}
    assert rows["public_a"][2] == 10  # template duration
    assert rows["public_b"][2] == 30  # the contact's own override


@pytest.mark.asyncio
async def test_field_values_only_come_from_visible_studies(client, studies):
    response = await client.get(f"{API}/catalog/results/fields/study.title/values")
    assert response.status_code == 200
    assert response.json() == ["public_a", "public_b"]


# --- Validation -------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "overrides",
    [
        {"dataset": "nope"},
        {"columns": ["study.title", "nope"]},
        {"columns": ["study.title", "study.title"]},
        {"filters": [{"field": "nope", "op": "eq", "value": 1}]},
        {"filters": [{"field": "study.title", "op": "gt", "value": 1}]},
        {"filters": [{"field": "result.dna_concentration", "op": "gt", "value": "abc"}]},
        {"filters": [{"field": "study.title", "op": "in", "value": []}]},
        {"filters": [{"field": "study.title", "op": "drop table", "value": 1}]},
        {"sort": [{"field": "nope"}]},
    ],
)
async def test_invalid_definitions_are_rejected(client, overrides):
    response = await client.post(f"{API}/preview", json=_definition(**overrides))
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_fields_need_their_table_joined(client, studies):
    base = {"dataset": "results", "columns": ["study.title", "donor_surface.label"]}
    response = await client.post(f"{API}/preview", json={**base, "joins": []})
    assert response.status_code == 422
    assert "Donor surface" in response.json()["detail"]

    # Joining a table also joins what it requires (donor surface -> contact).
    response = await client.post(f"{API}/preview", json={**base, "joins": ["donor_surface"]})
    assert response.status_code == 200, response.text
    assert sorted(r[1] for r in response.json()["rows"]) == ["public_a person", "public_b person"]

    filtered = {
        **base,
        "columns": ["study.title"],
        "joins": [],
        "filters": [{"field": "contact.duration", "op": "gt", "value": 0}],
    }
    assert (await client.post(f"{API}/preview", json=filtered)).status_code == 422


@pytest.mark.asyncio
async def test_unknown_join_is_rejected(client):
    response = await client.post(f"{API}/preview", json=_definition(joins=["nope"]))
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_required_tables_need_no_join(client, studies):
    response = await client.post(
        f"{API}/preview",
        json={"dataset": "results", "joins": [], "columns": ["study.title", "sample.name", "result.dna_concentration"]},
    )
    assert response.status_code == 200
    assert response.json()["total_rows"] == 2


@pytest.mark.asyncio
async def test_models_are_returned_with_their_joins(auth_client):
    # Saved without joins (as older models were): they're inferred on read.
    response = await auth_client.post(
        API, json={"name": "Old style", "definition": _definition(columns=["study.title", "donor_surface.label"])}
    )
    assert response.status_code == 201
    assert response.json()["definition"]["joins"] == ["contact", "donor_surface"]

    preset = (await auth_client.get(f"{API}/preset-transfer-results")).json()
    assert {"contact", "scenario", "donor_surface", "laboratory"} <= set(preset["definition"]["joins"])


@pytest.mark.asyncio
async def test_catalog_describes_tables(client):
    results = next(d for d in (await client.get(f"{API}/catalog")).json()["datasets"] if d["key"] == "results")
    tables = {t["key"]: t for t in results["tables"]}
    assert tables["study"]["required"] is True
    assert tables["donor_surface"]["requires"] == ["contact"]
    assert all(f["table"] in tables for f in results["fields"])


def test_presets_validate_against_catalog():
    for preset in PRESETS:
        validate_definition(preset.definition)


@pytest.mark.asyncio
async def test_catalog_lists_datasets(client):
    response = await client.get(f"{API}/catalog")
    assert response.status_code == 200
    keys = {d["key"] for d in response.json()["datasets"]}
    assert {"results", "pcr_profiles", "pcr_contributors", "contacts", "individuals", "studies"} <= keys


@pytest.mark.asyncio
@pytest.mark.parametrize("preset", PRESETS, ids=lambda p: p.id)
async def test_every_preset_runs(client, studies, preset):
    response = await client.post(
        f"{API}/preview", json=preset.definition.model_dump(mode="json")
    )
    assert response.status_code == 200, response.text


# --- Saved models -----------------------------------------------------------------


@pytest.mark.asyncio
async def test_saving_requires_an_account(client):
    response = await client.post(API, json={"name": "Mine", "definition": _definition()})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_saved_model_visibility_and_ownership(client, db_session, laboratory, regular_user):
    other = await _make_user(db_session, laboratory, email="other@example.com")

    _login(client, regular_user)
    private = await client.post(API, json={"name": "Private", "definition": _definition()})
    public = await client.post(
        API, json={"name": "Shared", "definition": _definition(), "is_public": True}
    )
    assert private.status_code == 201 and public.status_code == 201
    private_id, public_id = private.json()["id"], public.json()["id"]
    assert private.json()["source"] == "mine"

    listed = {m["id"]: m["source"] for m in (await client.get(API)).json()}
    assert listed[private_id] == "mine" and listed[public_id] == "mine"
    assert any(source == "preset" for source in listed.values())

    # Another user sees the public model, not the private one, and can't
    # change either.
    _login(client, other)
    listed = {m["id"]: m["source"] for m in (await client.get(API)).json()}
    assert listed.get(public_id) == "public"
    assert private_id not in listed
    assert (await client.get(f"{API}/{private_id}")).status_code == 404
    assert (await client.patch(f"{API}/{public_id}", json={"name": "Mine now"})).status_code == 403
    assert (await client.delete(f"{API}/{public_id}")).status_code == 403
    assert (await client.delete(f"{API}/{private_id}")).status_code == 404

    # Guests see the public one too.
    client.cookies.clear()
    listed = {m["id"] for m in (await client.get(API)).json()}
    assert public_id in listed and private_id not in listed

    # The owner can edit and delete.
    _login(client, regular_user)
    response = await client.patch(f"{API}/{private_id}", json={"name": "Renamed", "is_public": True})
    assert response.status_code == 200
    assert response.json()["name"] == "Renamed" and response.json()["is_public"] is True
    assert (await client.delete(f"{API}/{private_id}")).status_code == 204
    assert (await client.get(f"{API}/{private_id}")).status_code == 404


@pytest.mark.asyncio
async def test_invalid_definition_is_not_saved(auth_client):
    response = await auth_client.post(
        API, json={"name": "Broken", "definition": _definition(columns=["nope"])}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_study_ids_survive_saving(auth_client, studies):
    ids = [str(studies["public_a"].id)]
    response = await auth_client.post(
        API, json={"name": "Scoped", "definition": _definition(study_ids=ids)}
    )
    assert response.status_code == 201
    assert response.json()["definition"]["study_ids"] == ids


# --- Downloads --------------------------------------------------------------------


@pytest.mark.asyncio
async def test_csv_download(client, studies):
    response = await client.post(
        f"{API}/download?format=csv&name=My data", json=_definition()
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "transact-my-data-" in response.headers["content-disposition"]
    text = response.content.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(text)))
    assert rows[0] == ["Study title", "Scenario", "Duration (s)", "DNA concentration (ng/µl)"]
    assert sorted(r[0] for r in rows[1:]) == ["public_a", "public_b"]


@pytest.mark.asyncio
async def test_csv_download_with_key_headers(client, studies):
    response = await client.post(f"{API}/download?format=csv&header=key", json=_definition())
    header = response.content.decode("utf-8-sig").splitlines()[0]
    assert header == ",".join(_definition()["columns"])


@pytest.mark.asyncio
async def test_xlsx_download_has_data_and_citations(client, studies):
    response = await client.get(f"{API}/preset-transfer-results/download?format=xlsx")
    assert response.status_code == 200
    workbook = load_workbook(io.BytesIO(response.content), read_only=True)
    assert workbook.sheetnames == ["Data", "About"]
    data = list(workbook["Data"].iter_rows(values_only=True))
    assert data[0][0] == "Study title"
    assert len(data) == 3
    about = [row for row in workbook["About"].iter_rows(values_only=True)]
    cited = {row[0] for row in about if row and row[0]}
    assert {"public_a", "public_b"} <= cited
    assert "foreign" not in cited


@pytest.mark.asyncio
async def test_saved_model_download_is_live(auth_client, db_session, studies, categories, laboratory):
    response = await auth_client.post(API, json={"name": "Live", "definition": _definition()})
    model_id = response.json()["id"]

    async def count():
        r = await auth_client.get(f"{API}/{model_id}/download?format=csv")
        return len(r.content.decode("utf-8-sig").strip().splitlines()) - 1

    before = await count()
    await _seed_study(
        db_session, lab=laboratory, title="new_one", published=False, qc=False,
        category=categories["handling"], item_category=categories["knife"], concentration=9,
    )
    assert await count() == before + 1


@pytest.mark.asyncio
async def test_model_download_narrowed_to_selected_studies(client, studies):
    async def titles(query: str) -> list[str]:
        r = await client.get(f"{API}/preset-transfer-results/download?format=csv{query}")
        assert r.status_code == 200
        rows = list(csv.reader(io.StringIO(r.content.decode("utf-8-sig"))))
        return sorted(row[0] for row in rows[1:])

    a, b = studies["public_a"].id, studies["public_b"].id
    assert await titles("") == ["public_a", "public_b"]
    assert await titles(f"&study_ids={a}") == ["public_a"]
    assert await titles(f"&study_ids={a}&study_ids={b}") == ["public_a", "public_b"]
    # Selecting a study the viewer can't see doesn't widen access.
    assert await titles(f"&study_ids={studies['foreign'].id}") == []


@pytest.mark.asyncio
async def test_model_download_selection_never_widens_saved_scope(auth_client, studies):
    a, b = studies["public_a"].id, studies["public_b"].id
    response = await auth_client.post(
        API, json={"name": "Only A", "definition": _definition(study_ids=[str(a)])}
    )
    model_id = response.json()["id"]
    r = await auth_client.get(f"{API}/{model_id}/download?format=csv&study_ids={b}")
    assert r.status_code == 200
    assert len(r.content.decode("utf-8-sig").strip().splitlines()) == 1


@pytest.mark.asyncio
async def test_unknown_model_download_is_404(client):
    assert (await client.get(f"{API}/preset-nope/download")).status_code == 404
    assert (await client.get(f"{API}/not-a-uuid/download")).status_code == 404
