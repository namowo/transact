from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import (
    assert_manages_laboratory,
    current_lab_admin,
    current_optional_user,
    current_superuser,
    get_async_session,
)
from app.crud.laboratory import crud_laboratory as crud
from app.crud.user import crud_user
from app.models.user import User
from app.schemas.laboratory import (
    LaboratoryRead as ReadSchema,
    LaboratoryCreate as CreateSchema,
    LaboratoryUpdate as UpdateSchema,
)
from app.schemas.user import UserRead

router = APIRouter()


@router.get("", response_model=List[ReadSchema])
async def get_all(
    db: AsyncSession = Depends(get_async_session),
    user: Optional[User] = Depends(current_optional_user),
):
    if user and user.is_superuser:
        return await crud.get_all(db)
    return await crud.list_approved(db)


@router.get("/{id}", response_model=ReadSchema)
async def get_by_id(id: int, db: AsyncSession = Depends(get_async_session)):
    return await crud.get(db, id)


@router.post(
    "",
    response_model=ReadSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(current_superuser)],
)
async def create(obj_in: CreateSchema, db: AsyncSession = Depends(get_async_session)):
    # Superuser-only direct creation (e.g. seeding/import). Ordinary users
    # request a new laboratory via the lab-membership-requests endpoints.
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


@router.get("/{id}/users", response_model=List[UserRead])
async def get_lab_users(
    id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_lab_admin),
):
    assert_manages_laboratory(user, id)
    return await crud_user.list_by_laboratory(db, id)
