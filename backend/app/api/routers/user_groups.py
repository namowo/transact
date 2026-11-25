from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_active_user, get_async_session
from app.core.permission_catalog import PERMISSIONS, Permission
from app.crud import user_group as crud
from app.models.user import User
from app.models.user_group import UserGroup
from app.schemas.user_group import (
    PermissionRead,
    UserGroupCreate,
    UserGroupRead,
    UserGroupUpdate,
)

router = APIRouter()
permissions_router = APIRouter()


@permissions_router.get("", response_model=List[PermissionRead])
async def list_permissions():
    """Every permission a group can grant."""
    return [
        PermissionRead(
            key=info.key, label=info.label, description=info.description, scope=info.scope
        )
        for info in PERMISSIONS
    ]


def _manages_any_groups(user: User) -> bool:
    return (
        user.can(Permission.MANAGE_GROUPS)
        or user.can(Permission.MANAGE_USERS)
        or user.can(Permission.MANAGE_LAB_GROUPS)
        or user.can(Permission.MANAGE_LAB_MEMBERS)
    )


async def _read(db: AsyncSession, groups: List[UserGroup]) -> List[UserGroupRead]:
    counts = await crud.member_counts(db, [group.id for group in groups])
    return [
        UserGroupRead.model_validate(group).model_copy(
            update={"member_count": counts.get(group.id, 0)}
        )
        for group in groups
    ]


@router.get("", response_model=List[UserGroupRead])
async def list_groups(
    laboratory_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """Platform-wide groups plus the laboratory groups the user may see;
    with `laboratory_id`, only that laboratory's groups besides the
    platform-wide ones."""
    if not _manages_any_groups(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    await crud.ensure_system_groups(db)
    return await _read(db, await crud.list_visible(db, user, laboratory_id))


@router.post("", response_model=UserGroupRead, status_code=status.HTTP_201_CREATED)
async def create_group(
    obj_in: UserGroupCreate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    group = await crud.create(
        db,
        user,
        name=obj_in.name,
        description=obj_in.description,
        permissions=obj_in.permissions,
        laboratory_id=obj_in.laboratory_id,
    )
    return (await _read(db, [group]))[0]


@router.patch("/{id}", response_model=UserGroupRead)
async def update_group(
    id: UUID,
    obj_in: UserGroupUpdate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    group = await crud.get(db, id)
    group = await crud.update(
        db,
        user,
        group,
        name=obj_in.name,
        description=obj_in.description,
        permissions=obj_in.permissions,
        fields_set=obj_in.model_fields_set,
    )
    return (await _read(db, [group]))[0]


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    group = await crud.get(db, id)
    await crud.delete_group(db, user, group)
