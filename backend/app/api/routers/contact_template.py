from typing import List

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import permissions as P
from app.core.deps import current_data_editor, get_async_session
from app.models.user import User
from app.crud.contact_template import crud_contact_template as crud
from app.schemas.contact_template import (
    ContactTemplateRead as ReadSchema,
    ContactTemplateCreate as CreateSchema,
    ContactTemplateUpdate as UpdateSchema,
)

router = APIRouter()


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
    user: User = Depends(current_data_editor),
):
    await P.assert_can_edit_studies(db, user, await P.study_ids_of_scenarios(db, obj_in.scenario_ids))
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
    await P.assert_can_edit_studies(
        db, user, (await P.study_ids_of_contact_template(db, id)) | (await P.study_ids_of_scenarios(db, obj_in.scenario_ids or []))
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
    await P.assert_can_edit_studies(db, user, await P.study_ids_of_contact_template(db, id))
    await crud.delete(db, id)
