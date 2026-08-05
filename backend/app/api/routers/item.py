from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_superuser, get_async_session
from app.crud.item import crud_item as crud
from app.schemas.item import (
    ItemGroup,
    ItemRead as ReadSchema,
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

    groups: dict[int | None, ItemGroup] = {}
    for item in items:
        key = item.item_category_id
        if key not in groups:
            label = item.item_category.name if item.item_category else "Uncategorized"
            groups[key] = ItemGroup(label=label or "Uncategorized", value=key, items=[])
        groups[key].items.append(ReadSchema.model_validate(item))

    return list(groups.values())


@router.get("/{id}", response_model=ReadSchema)
async def get_by_id(id: int, db: AsyncSession = Depends(get_async_session)):
    return await crud.get(db, id)


@router.post(
    "",
    response_model=ReadSchema,
    dependencies=[Depends(current_superuser)],
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
    id: int, obj_in: UpdateSchema, db: AsyncSession = Depends(get_async_session)
):
    return await crud.update(db, id, obj_in)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(current_superuser)],
)
async def delete(id: int, db: AsyncSession = Depends(get_async_session)):
    await crud.delete(db, id)
