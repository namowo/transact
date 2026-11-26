"""Ownership checks for study data.

A study belongs to the laboratory that created it. Anyone may view a
published study. Changing a study - or the records that hang off it
(scenarios, samples, results, ...) - is reserved to:

- members of the owning laboratory. Any member may edit the study itself;
  its data additionally needs the "Enter study data" permission.
- users with "Edit data of all laboratories" (platform admins preparing data
  for a laboratory), unless the laboratory has switched that off
  (Laboratory.allow_admin_data_entry).

Nothing else - including managing users or laboratories - grants access to
another laboratory's research data.
"""

from typing import Iterable, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permission_catalog import Permission
from app.models.laboratory import Laboratory
from app.models.study import Study
from app.models.user import User

EDIT_FORBIDDEN_MESSAGE = "You can only edit studies belonging to your own laboratory."
DATA_FORBIDDEN_MESSAGE = "You are not allowed to enter data for this study."


def acts_for_laboratory(
    user: Optional[User], laboratory: Optional[Laboratory]
) -> bool:
    """Whether `user` may work on `laboratory`'s data although they aren't a
    member of it."""
    return (
        user is not None
        and laboratory is not None
        and laboratory.allow_admin_data_entry
        and user.can(Permission.EDIT_ALL_LABORATORY_DATA)
    )


def _is_member(user: Optional[User], laboratory_id: Optional[UUID]) -> bool:
    return (
        user is not None
        and user.laboratory_id is not None
        and laboratory_id == user.laboratory_id
    )


def can_edit_study(study: Study, user: Optional[User]) -> bool:
    """Whether `user` may edit the study itself (title, design, ...)."""
    return _is_member(user, study.laboratory_id) or acts_for_laboratory(
        user, study.laboratory
    )


def can_enter_study_data(study: Study, user: Optional[User]) -> bool:
    """Whether `user` may add and change the study's data."""
    if _is_member(user, study.laboratory_id) and user.can(Permission.ENTER_DATA):
        return True
    return acts_for_laboratory(user, study.laboratory)


def can_view_study(study: Study, user: Optional[User]) -> bool:
    if study.published:
        return True
    if user is None:
        return False
    return (
        user.can(Permission.VIEW_ALL_STUDIES)
        or _is_member(user, study.laboratory_id)
        or acts_for_laboratory(user, study.laboratory)
        or can_review_study(study, user)
    )


def can_review_study(study: Study, user: Optional[User]) -> bool:
    """Whether `user` may review the study as a quality checker: once its
    laboratory submitted it (it isn't a draft any more)."""
    return (
        user is not None
        and user.can(Permission.QUALITY_CHECK)
        and (study.review_status or "draft") != "draft"
    )


def can_create_study_for(user: User, laboratory: Optional[Laboratory]) -> bool:
    if laboratory is None:
        return False
    return _is_member(user, laboratory.id) or acts_for_laboratory(user, laboratory)


def assert_can_edit_study(study: Study, user: User) -> None:
    if not can_edit_study(study, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=EDIT_FORBIDDEN_MESSAGE
        )


async def assert_can_edit_studies(
    db: AsyncSession, user: User, study_ids: Iterable[Optional[UUID]]
) -> None:
    """Raise 403 unless `user` may enter data for every study in `study_ids`.

    `None` entries (records not attached to a study) are ignored.
    """
    ids = {study_id for study_id in study_ids if study_id is not None}
    if not ids:
        return
    result = await db.execute(
        select(Study.laboratory_id, Laboratory.allow_admin_data_entry)
        .outerjoin(Laboratory, Laboratory.id == Study.laboratory_id)
        .where(Study.id.in_(ids))
    )
    for laboratory_id, allow_admin_data_entry in result.all():
        if _is_member(user, laboratory_id) and user.can(Permission.ENTER_DATA):
            continue
        if allow_admin_data_entry and user.can(Permission.EDIT_ALL_LABORATORY_DATA):
            continue
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=DATA_FORBIDDEN_MESSAGE
        )


# --- Resolving which studies a record belongs to --------------------------
#
# Each resolver returns the ids of the studies whose data a record is part
# of. Records that are not tied to any study (e.g. an unused catalog item)
# resolve to an empty set and are not restricted by laboratory.


async def study_ids_of_sample(db: AsyncSession, sample_id: Optional[UUID]) -> set:
    from app.models.sample import Sample

    if sample_id is None:
        return set()
    result = await db.execute(select(Sample.study_id).where(Sample.id == sample_id))
    return set(result.scalars())


async def study_ids_of_individual(
    db: AsyncSession, individual_id: Optional[UUID]
) -> set:
    from app.models.individual import Individual

    if individual_id is None:
        return set()
    result = await db.execute(
        select(Individual.study_id).where(Individual.id == individual_id)
    )
    return set(result.scalars())


async def study_ids_of_surface_template(
    db: AsyncSession, surface_template_id: Optional[UUID]
) -> set:
    """The studies owning the scenarios whose contact templates use this
    surface template as donor or recipient.

    The item a surface template references is deliberately not considered:
    items are a shared catalog, and referencing one doesn't change it."""
    from sqlalchemy import or_

    from app.models.contact_template import ContactTemplate, scenario_contact_template

    if surface_template_id is None:
        return set()
    result = await db.execute(
        select(scenario_contact_template.c.scenario_id)
        .join(
            ContactTemplate,
            ContactTemplate.id == scenario_contact_template.c.contact_template_id,
        )
        .where(
            or_(
                ContactTemplate.donor_surface_template_id == surface_template_id,
                ContactTemplate.recipient_surface_template_id == surface_template_id,
            )
        )
    )
    return await study_ids_of_scenarios(db, result.scalars())


async def study_ids_of_scenarios(db: AsyncSession, scenario_ids: Iterable[UUID]) -> set:
    """The owning studies of the given scenarios."""
    from app.models.scenario import Scenario

    ids = set(scenario_ids)
    if not ids:
        return set()
    result = await db.execute(
        select(Scenario.owning_study_id).where(Scenario.id.in_(ids))
    )
    return set(result.scalars())


async def study_ids_of_contact_template(
    db: AsyncSession, contact_template_id: Optional[UUID]
) -> set:
    from app.models.contact_template import scenario_contact_template

    if contact_template_id is None:
        return set()
    result = await db.execute(
        select(scenario_contact_template.c.scenario_id).where(
            scenario_contact_template.c.contact_template_id == contact_template_id
        )
    )
    return await study_ids_of_scenarios(db, result.scalars())


async def study_ids_of_surface(db: AsyncSession, surface_id: Optional[UUID]) -> set:
    from app.models.sample import Sample
    from app.models.surface import Surface

    if surface_id is None:
        return set()
    ids = set()
    surface = await db.get(Surface, surface_id)
    if surface is not None:
        ids |= await study_ids_of_individual(db, surface.individual_id)
    result = await db.execute(select(Sample.study_id).where(Sample.surface_id == surface_id))
    ids |= set(result.scalars())
    return ids


async def study_ids_of_contact(db: AsyncSession, contact_id: Optional[UUID]) -> set:
    from app.models.contact import Contact
    from app.models.sample import Sample

    if contact_id is None:
        return set()
    contact = await db.get(Contact, contact_id)
    if contact is None:
        return set()
    ids = await study_ids_of_surface(db, contact.donor_surface_id)
    ids |= await study_ids_of_surface(db, contact.recipient_surface_id)
    result = await db.execute(select(Sample.study_id).where(Sample.contact_id == contact_id))
    ids |= set(result.scalars())
    return ids


async def study_ids_of_result(db: AsyncSession, result_id: Optional[UUID]) -> set:
    from app.models.result import Result

    if result_id is None:
        return set()
    result = await db.execute(select(Result.sample_id).where(Result.id == result_id))
    return await study_ids_of_sample(db, result.scalars().first())


async def assert_can_change_study_links(
    db: AsyncSession,
    user: User,
    current: Iterable[UUID],
    requested: Optional[Iterable[UUID]],
) -> None:
    """Linking/unlinking a shared record (scenario, item) to studies only
    touches the studies being added or removed, so only those need to be
    editable. `requested=None` means the links are left unchanged."""
    if requested is None:
        return
    await assert_can_edit_studies(db, user, set(current) ^ set(requested))
