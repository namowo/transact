from typing import Iterable, List, Optional

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import permissions as P
from app.crud.study_scope import scenario_ids_of_study
from app.core.deps import current_data_editor, get_async_session
from app.models.contact_template import ContactTemplate
from app.models.scenario import Scenario
from app.models.study import Study
from app.models.user import User
from app.crud.scenario import crud_scenario as crud
from app.schemas.scenario import (
    ScenarioRead as ReadSchema,
    ScenarioCreate as CreateSchema,
    ScenarioUpdate as UpdateSchema,
)

router = APIRouter()


def _owners(scenario: Scenario) -> set:
    # Scenarios created before ownership was tracked belong to every study
    # that links them.
    if scenario.owning_study_id is not None:
        return {scenario.owning_study_id}
    return {study.id for study in scenario.studies}


def _name_key(name: Optional[str]) -> str:
    return " ".join((name or "").split()).casefold()


async def _assert_unique_name(
    db: AsyncSession,
    name: Optional[str],
    study_ids: Iterable[UUID],
    exclude_id: Optional[UUID] = None,
) -> None:
    """Scenario names must be unique among the scenarios of a study (ignoring
    case and spacing), since scenarios are picked by name - e.g. in the Excel
    planning sheet."""
    study_ids = set(study_ids)
    if not study_ids or not _name_key(name):
        return
    stmt = select(Study.title, Scenario.name).join(Study.scenarios).where(Study.id.in_(study_ids))
    if exclude_id is not None:
        stmt = stmt.where(Scenario.id != exclude_id)
    result = await db.execute(stmt)
    for study_title, other_name in result.all():
        if _name_key(other_name) == _name_key(name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"The study '{study_title or 'Untitled'}' already has a scenario named "
                    f"'{other_name}'. Please choose a different name."
                ),
            )


@router.get("", response_model=List[ReadSchema])
async def get_all(
    study_id: Optional[UUID] = None, db: AsyncSession = Depends(get_async_session)
):
    if study_id is not None:
        return await crud.get_all_where(
            db,
            Scenario.id.in_(scenario_ids_of_study(study_id)),
            # Neither collection is part of ScenarioRead, and loading them
            # pulls in every contact and sample with all their details.
            options=[
                selectinload(Scenario.studies).noload(Study.samples),
                selectinload(Scenario.contact_templates).noload(ContactTemplate.contacts),
            ],
        )
    return await crud.get_all(db)


@router.get("/{id}", response_model=ReadSchema)
async def get_by_id(id: UUID, db: AsyncSession = Depends(get_async_session)):
    return await crud.get(db, id)


@router.post(
    "",
    response_model=ReadSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create(
    obj_in: CreateSchema,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_data_editor),
):
    await P.assert_can_edit_studies(
        db, user, {obj_in.owning_study_id, *obj_in.study_ids}
    )
    await _assert_unique_name(
        db, obj_in.name, {*obj_in.study_ids, obj_in.owning_study_id} - {None}
    )
    return await crud.create(db, obj_in)


@router.patch(
    "/{id}",
    response_model=ReadSchema,
)
async def update(
    id: UUID,
    obj_in: UpdateSchema,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_data_editor),
):
    scenario = await crud.get(db, id)
    # Other studies may link a scenario into their planning, but only the
    # owning study may change the scenario itself.
    if obj_in.model_fields_set - {"study_ids"}:
        await P.assert_can_edit_studies(db, user, _owners(scenario))
    await P.assert_can_change_study_links(
        db, user, (study.id for study in scenario.studies), obj_in.study_ids
    )
    current_study_ids = {study.id for study in scenario.studies}
    target_study_ids = set(obj_in.study_ids) if obj_in.study_ids is not None else current_study_ids
    if "name" in obj_in.model_fields_set and _name_key(obj_in.name) != _name_key(scenario.name):
        # Renamed: the new name must be free in every study it's linked to.
        await _assert_unique_name(db, obj_in.name, target_study_ids, exclude_id=scenario.id)
    else:
        # Only check studies it's newly linked to, so existing duplicates
        # don't block unrelated edits.
        await _assert_unique_name(
            db, scenario.name, target_study_ids - current_study_ids, exclude_id=scenario.id
        )
    return await crud.update(db, id, obj_in)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete(
    id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_data_editor),
):
    scenario = await crud.get(db, id)
    await P.assert_can_edit_studies(db, user, _owners(scenario))
    await crud.delete(db, id)
