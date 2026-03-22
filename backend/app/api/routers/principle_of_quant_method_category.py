from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_superuser, get_async_session
from app.crud.principle_of_quant_method_category import crud_principle_of_quant_method_category as crud
from app.schemas.principle_of_quant_method_category import (
    PrincipleOfQuantMethodCategoryRead as ReadSchema,
    PrincipleOfQuantMethodCategoryCreate as CreateSchema,
    PrincipleOfQuantMethodCategoryUpdate as UpdateSchema,
)

router = APIRouter()


@router.get("", response_model=List[ReadSchema])
async def get_all(db: AsyncSession = Depends(get_async_session)):
    return await crud.get_all(db)


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
