from typing import List

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_active_user, current_superuser, get_async_session
from app.crud.item_category import crud_item_category as crud
from app.schemas.item_category import (
    ItemCategoryRead as ReadSchema,
    ItemCategoryCreate as CreateSchema,
    ItemCategoryUpdate as UpdateSchema,
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
    # Item categories/subcategories are freely extensible lookups - any
    # active user may add new ones while planning, unlike other category
    # tables that stay superuser-managed.
    dependencies=[Depends(current_active_user)],
    status_code=status.HTTP_201_CREATED,
)
async def create(obj_in: CreateSchema, db: AsyncSession = Depends(get_async_session)):
    return await crud.create(db, obj_in)


@router.patch(
    "/{id}",
    response_model=ReadSchema,
    dependencies=[Depends(current_superuser)],
)
async def update(
    id: UUID, obj_in: UpdateSchema, db: AsyncSession = Depends(get_async_session)
):
    return await crud.update(db, id, obj_in)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser)],
)
async def delete(id: UUID, db: AsyncSession = Depends(get_async_session)):
    await crud.delete(db, id)
