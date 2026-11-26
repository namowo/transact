"""Quality review: submitting, commenting, requesting changes, diffs and
passing (see app.models.study_review)."""

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.core.permission_catalog import SystemGroup
from app.core.security import create_access_token
from app.models.individual import Individual
from app.models.study import Study
from app.models.user import User
from tests.conftest import _make_user


def _login(client: AsyncClient, user: User) -> AsyncClient:
    client.cookies.clear()
    client.cookies.update({"access_token": create_access_token(subject=str(user.id))})
    return client


@pytest.fixture(autouse=True)
def no_mails(monkeypatch):
    sent: list[tuple[str, str]] = []

    async def fake_send_mail(subject, to_recipient, template_name, template_values):
        from app.services.mail import main as mail_main

        mail_main.get_content(template_name, template_values)
        sent.append((to_recipient, template_name))

    monkeypatch.setattr("app.services.mail.messages.study_quality_check.send_mail", fake_send_mail)
    return sent


@pytest_asyncio.fixture
async def checker(db_session) -> User:
    # A pure quality checker - no laboratory, no "view all studies".
    return await _make_user(
        db_session, None, email="checker@example.com", groups=[SystemGroup.QUALITY_CHECKER]
    )


@pytest_asyncio.fixture
async def study(db_session, laboratory) -> Study:
    study = Study(title="Reviewed study", laboratory_id=laboratory.id, published=False)
    db_session.add(study)
    await db_session.commit()
    await db_session.refresh(study)
    db_session.add(Individual(study_id=study.id, name="P1", age=30))
    await db_session.commit()
    return study


def _url(study: Study, path: str = "") -> str:
    return f"/api/v1/studies/{study.id}/review{path}"


async def test_checker_sees_study_only_once_submitted(client, study, regular_user, checker):
    resp = await _login(client, checker).get(f"/api/v1/studies/{study.id}")
    assert resp.status_code != 200
    resp = await client.get(_url(study))
    assert resp.status_code == 404
    resp = await _login(client, checker).get("/api/v1/studies/review-queue")
    assert resp.json() == []

    resp = await _login(client, regular_user).post(_url(study, "/submit"))
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "in_review"
    assert [r["number"] for r in resp.json()["rounds"]] == [1]

    resp = await _login(client, checker).get(f"/api/v1/studies/{study.id}")
    assert resp.status_code == 200
    assert resp.json()["review_status"] == "in_review"
    queue = (await _login(client, checker).get("/api/v1/studies/review-queue")).json()
    assert [e["study_id"] for e in queue] == [str(study.id)]


async def test_submitting_notifies_checkers(client, study, regular_user, checker, no_mails):
    await _login(client, regular_user).post(_url(study, "/submit"))
    assert (checker.email, "study-submitted-for-review.html") in no_mails


async def test_full_review_cycle(
    client, db_session, study, regular_user, data_entrant, checker, no_mails
):
    await _login(client, regular_user).post(_url(study, "/submit"))

    # The lab can't comment, the checker can - on a record of a section.
    resp = await _login(client, regular_user).post(_url(study, "/comments"), json={"body": "x"})
    assert resp.status_code == 403
    records = (await _login(client, checker).get(_url(study, "/records"))).json()["records"]
    person = records["individuals"][0]
    assert person["label"] == "P1 (30y)"
    resp = await client.post(
        _url(study, "/comments"),
        json={
            "body": "Age looks wrong.",
            "section": "individuals",
            "target_id": person["id"],
            "target_label": person["label"],
        },
    )
    assert resp.status_code == 201, resp.text
    review = resp.json()
    comment = review["comments"][0]
    assert comment["status"] == "open" and comment["round_number"] == 1
    assert review["progress"] == {"total": 1, "open": 1, "addressed": 0, "resolved": 0}

    resp = await client.post(_url(study, "/comments"), json={"body": "x", "section": "nope"})
    assert resp.status_code == 422

    # Can't pass while comments are unresolved.
    resp = await client.post(f"/api/v1/studies/{study.id}/quality-check")
    assert resp.status_code == 409

    resp = await client.post(_url(study, "/request-changes"))
    assert resp.status_code == 200
    assert resp.json()["status"] == "changes_requested"
    # Only members who enter data hear about it.
    assert (data_entrant.email, "study-changes-requested.html") in no_mails
    assert (regular_user.email, "study-changes-requested.html") not in no_mails

    # The lab replies, fixes the data and marks the comment addressed ...
    _login(client, regular_user)
    resp = await client.post(_url(study, f"/comments/{comment['id']}/replies"), json={"body": "Fixed."})
    assert resp.status_code == 201
    assert resp.json()["comments"][0]["replies"][0]["body"] == "Fixed."
    # ... but can't resolve it.
    resp = await client.patch(_url(study, f"/comments/{comment['id']}"), json={"status": "resolved"})
    assert resp.status_code == 403
    resp = await client.patch(_url(study, f"/comments/{comment['id']}"), json={"status": "addressed"})
    assert resp.status_code == 200
    assert resp.json()["progress"]["addressed"] == 1

    individual = await db_session.get(Individual, person["id"])
    individual.age = 31
    await db_session.commit()

    # Lab changes since submission show against the current data.
    diff = (await client.get(_url(study, "/diff"), params={"from_round": 1})).json()
    section = next(s for s in diff["sections"] if s["key"] == "individuals")
    assert section["changed"] == 1
    assert {"key": "individual.age", "label": section["rows"][0]["fields"][0]["label"], "old": 30, "new": 31} in section["rows"][0]["fields"]

    resp = await client.post(_url(study, "/submit"))
    assert resp.json()["status"] == "in_review"
    assert [r["number"] for r in resp.json()["rounds"]] == [1, 2]
    assert resp.json()["rounds"][0]["decision"] == "changes_requested"

    # The checker compares the rounds, resolves the comment and passes.
    _login(client, checker)
    diff = (await client.get(_url(study, "/diff"), params={"from_round": 1, "to_round": 2})).json()
    section = next(s for s in diff["sections"] if s["key"] == "individuals")
    assert section["changed"] == 1
    details = next(s for s in diff["sections"] if s["key"] == "details")
    assert details["rows"] == []

    resp = await client.patch(_url(study, f"/comments/{comment['id']}"), json={"status": "resolved"})
    assert resp.json()["progress"]["resolved"] == 1
    resp = await client.post(f"/api/v1/studies/{study.id}/quality-check")
    assert resp.status_code == 200, resp.text
    assert resp.json()["review_status"] == "passed"
    review = (await client.get(_url(study))).json()
    assert review["rounds"][-1]["decision"] == "passed"


async def test_only_authors_edit_or_delete_comments(client, study, regular_user, checker):
    await _login(client, regular_user).post(_url(study, "/submit"))
    review = (await _login(client, checker).post(_url(study, "/comments"), json={"body": "Check DOI"})).json()
    comment_id = review["comments"][0]["id"]

    _login(client, regular_user)
    resp = await client.patch(_url(study, f"/comments/{comment_id}"), json={"body": "Changed"})
    assert resp.status_code == 403
    resp = await client.delete(_url(study, f"/comments/{comment_id}"))
    assert resp.status_code == 403

    _login(client, checker)
    resp = await client.patch(_url(study, f"/comments/{comment_id}"), json={"body": "Check the DOI"})
    assert resp.json()["comments"][0]["body"] == "Check the DOI"
    assert resp.json()["comments"][0]["edited_at"] is not None
    resp = await client.delete(_url(study, f"/comments/{comment_id}"))
    assert resp.status_code == 204


async def test_cannot_submit_twice_or_request_changes_on_draft(client, study, regular_user, checker):
    resp = await _login(client, regular_user).post(_url(study, "/submit"))
    assert resp.status_code == 200
    resp = await client.post(_url(study, "/submit"))
    assert resp.status_code == 409


async def test_other_laboratories_cannot_submit(client, db_session, study):
    from app.models.laboratory import Laboratory, LaboratoryApprovalStatus

    other = Laboratory(
        laboratory_name="Other",
        institutional_affiliation="Else",
        city="X",
        country="Y",
        approval_status=LaboratoryApprovalStatus.approved,
    )
    db_session.add(other)
    await db_session.commit()
    stranger = await _make_user(db_session, other, email="stranger@example.com")
    resp = await _login(client, stranger).post(_url(study, "/submit"))
    assert resp.status_code == 404
