"""Contacts with the same tool use the same kind of item, never the identical
surface ("das gleiche, aber nicht dasselbe")."""

import pytest
from fastapi import HTTPException

from app.crud.contact import crud_contact
from app.models.contact_template import ContactTemplate
from app.models.item import Item
from app.models.surface import Surface
from app.models.surface_template import SurfaceTemplate
from app.schemas.contact import ContactCreate, ContactUpdate


async def _setup(db):
    item = Item(description="Mug")
    db.add(item)
    await db.flush()
    item_template = SurfaceTemplate(item_id=item.id)
    person_template = SurfaceTemplate()
    db.add_all([item_template, person_template])
    await db.flush()
    contact_template = ContactTemplate(
        donor_surface_template_id=person_template.id,
        recipient_surface_template_id=item_template.id,
    )
    db.add(contact_template)
    await db.flush()

    def surface(template):
        s = Surface(surface_template_id=template.id)
        db.add(s)
        return s

    surfaces = {
        "mug1": surface(item_template),
        "mug2": surface(item_template),
        "hand1": surface(person_template),
        "hand2": surface(person_template),
    }
    await db.commit()
    return contact_template, surfaces


def _create(template, donor, recipient):
    return ContactCreate(
        contact_template_id=template.id,
        donor_surface_id=donor.id,
        recipient_surface_id=recipient.id,
    )


@pytest.mark.asyncio
async def test_item_surface_cannot_be_shared_between_contacts(db_session):
    template, s = await _setup(db_session)
    await crud_contact.create(db_session, _create(template, s["hand1"], s["mug1"]))

    with pytest.raises(HTTPException) as exc:
        await crud_contact.create(db_session, _create(template, s["hand2"], s["mug1"]))
    assert exc.value.status_code == 409

    # The same kind of item, but its own surface, is fine.
    await crud_contact.create(db_session, _create(template, s["hand2"], s["mug2"]))


@pytest.mark.asyncio
async def test_update_cannot_switch_to_a_used_item_surface(db_session):
    template, s = await _setup(db_session)
    await crud_contact.create(db_session, _create(template, s["hand1"], s["mug1"]))
    second = await crud_contact.create(db_session, _create(template, s["hand2"], s["mug2"]))

    with pytest.raises(HTTPException) as exc:
        await crud_contact.update(
            db_session, second.id, ContactUpdate(recipient_surface_id=s["mug1"].id)
        )
    assert exc.value.status_code == 409

    # Changing only the other side does not re-check the untouched item side.
    await crud_contact.update(
        db_session, second.id, ContactUpdate(donor_surface_id=s["hand1"].id)
    )


@pytest.mark.asyncio
async def test_surface_cannot_be_donor_and_recipient(db_session):
    template, s = await _setup(db_session)
    with pytest.raises(HTTPException) as exc:
        await crud_contact.create(db_session, _create(template, s["hand1"], s["hand1"]))
    assert exc.value.status_code == 409
