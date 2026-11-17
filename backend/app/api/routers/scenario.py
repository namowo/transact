from typing import List

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import permissions as P
from app.core.deps import current_superuser, get_async_session
from app.models.scenario import Scenario
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


@router.get("", response_model=List[ReadSchema])
async def get_all(db: AsyncSession = Depends(get_async_session)):
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
    user: User = Depends(current_superuser),
):
    await P.assert_can_edit_studies(
        db, user, {obj_in.owning_study_id, *obj_in.study_ids}
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
    user: User = Depends(current_superuser),
):
    scenario = await crud.get(db, id)
    # Other studies may link a scenario into their planning, but only the
    # owning study may change the scenario itself.
    if obj_in.model_fields_set - {"study_ids"}:
        await P.assert_can_edit_studies(db, user, _owners(scenario))
    await P.assert_can_change_study_links(
        db, user, (study.id for study in scenario.studies), obj_in.study_ids
    )
    return await crud.update(db, id, obj_in)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete(
    id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_superuser),
):
    scenario = await crud.get(db, id)
    await P.assert_can_edit_studies(db, user, _owners(scenario))
    await crud.delete(db, id)
