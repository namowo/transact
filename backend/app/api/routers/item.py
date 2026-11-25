from typing import List

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import permissions as P
from app.core.deps import current_data_editor, get_async_session
from app.models.user import User
from app.crud.item import crud_item as crud
from app.schemas.item import (
    ItemGroup,
    ItemRead as ReadSchema,
    ItemReadNested,
    ItemCreate as CreateSchema,
    ItemUpdate as UpdateSchema,
)

router = APIRouter()


@router.get("", response_model=List[ReadSchema])
async def get_all(db: AsyncSession = Depends(get_async_session)):
    return await crud.get_all(db)


@router.get("/grouped", response_model=List[ItemGroup])
async def get_all_grouped(db: AsyncSession = Depends(get_async_session)):
    """Items grouped by item_category, for a grouped Select. Items without
    a category are placed in a trailing "Uncategorized" group."""
    items = await crud.get_all_grouped_by_category(db)

    groups: dict[UUID | None, ItemGroup] = {}
    for item in items:
        key = item.item_category_id
        if key not in groups:
            label = item.item_category.name if item.item_category else "Uncategorized"
            groups[key] = ItemGroup(label=label or "Uncategorized", value=key, items=[])
        groups[key].items.append(ItemReadNested.model_validate(item))

    return list(groups.values())


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
    await P.assert_can_edit_studies(db, user, obj_in.study_ids)
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
    item = await crud.get(db, id)
    linked = {study.id for study in item.studies}
    # Items are a shared catalog: any study may link one, but changing the
    # item itself affects every study using it, so all of them must be ours.
    if obj_in.model_fields_set - {"study_ids", "scenario_ids"}:
        await P.assert_can_edit_studies(db, user, linked)
    await P.assert_can_change_study_links(db, user, linked, obj_in.study_ids)
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
    item = await crud.get(db, id)
    await P.assert_can_edit_studies(db, user, {study.id for study in item.studies})
    await crud.delete(db, id)
