from typing import List, Optional

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import permissions as P
from app.crud.study_scope import sample_in_study
from app.core.deps import current_superuser, get_async_session
from app.models.user import User
from app.crud.sample import crud_sample as crud
from app.schemas.sample import (
    SampleRead as ReadSchema,
    SampleCreate as CreateSchema,
    SampleUpdate as UpdateSchema,
)

router = APIRouter()


@router.get("", response_model=List[ReadSchema])
async def get_all(
    study_id: Optional[UUID] = None, db: AsyncSession = Depends(get_async_session)
):
    if study_id is not None:
        return await crud.get_all_where(db, sample_in_study(study_id))
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
    await P.assert_can_edit_studies(db, user, {obj_in.study_id})
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
    await P.assert_can_edit_studies(
        db, user, (await P.study_ids_of_sample(db, id)) | ({obj_in.study_id})
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
    await P.assert_can_edit_studies(db, user, await P.study_ids_of_sample(db, id))
    await crud.delete(db, id)
