from typing import List, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import (
    assert_manages_laboratory,
    current_active_user,
    current_member_manager,
    current_user_manager,
    get_async_session,
)
from app.core.permission_catalog import Permission
from app.crud import user_group as user_groups
from app.core.security import verify_password
from app.crud.base import CRUDBase
from app.crud.user import crud_user
from app.models.user import User
from app.schemas.user import (
    EmailChange,
    LaboratoryAssignment,
    PasswordChange,
    UserRead,
    UserUpdate,
)
from app.schemas.user_group import UserGroupAssignment

router = APIRouter()


def assert_manages_laboratory_or_users(actor: User, target: User) -> None:
    """Admins manage every account; lab admins the members of their lab."""
    if actor.can(Permission.MANAGE_USERS):
        return
    if target.laboratory_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage users in your own laboratory.",
        )
    assert_manages_laboratory(actor, target.laboratory_id)

_crud_user_update = CRUDBase(User)


@router.get(
    "",
    response_model=List[UserRead],
    dependencies=[Depends(current_user_manager)],
)
async def list_users(db: AsyncSession = Depends(get_async_session)):
    return await crud_user.list_all(db)


@router.get("/me", response_model=UserRead)
async def read_me(user: User = Depends(current_active_user)):
    return user


@router.patch("/me", response_model=UserRead)
async def update_me(
    obj_in: UserUpdate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    return await _crud_user_update.update(db, user.id, obj_in)


@router.post("/me/change-password", response_model=UserRead)
async def change_password(
    obj_in: PasswordChange,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    if not verify_password(obj_in.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )
    return await crud_user.set_password(db, user, obj_in.new_password)


@router.post("/me/change-email", response_model=UserRead)
async def change_email(
    obj_in: EmailChange,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    if not verify_password(obj_in.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )
    existing = await crud_user.get_by_email(db, obj_in.new_email)
    if existing is not None and existing.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )
    return await crud_user.set_email(db, user, obj_in.new_email)


@router.post("/me/dismiss-passkey-prompt", response_model=UserRead)
async def dismiss_passkey_prompt(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    return await crud_user.dismiss_passkey_prompt(db, user)


# Interactive guides the frontend knows about.
TourId = Literal["onboarding", "new-study", "data-entry"]


@router.post("/me/completed-tours/{tour}", response_model=UserRead)
async def complete_tour(
    tour: TourId,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    return await crud_user.complete_tour(db, user, tour)


@router.put("/{id}/groups", response_model=UserRead)
async def set_groups(
    id: UUID,
    obj_in: UserGroupAssignment,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_member_manager),
):
    """Replace the user's groups. Only the groups that change are checked:
    see app.crud.user_group for who may assign which group."""
    target = await crud_user.get(db, id)
    assert_manages_laboratory_or_users(user, target)
    return await user_groups.set_user_groups(db, user, target, obj_in.group_ids)


@router.post("/{id}/remove-from-laboratory", response_model=UserRead)
async def remove_from_laboratory(
    id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_member_manager),
):
    target = await crud_user.get(db, id)
    assert_manages_laboratory(user, target.laboratory_id)
    if target.can(Permission.MANAGE_LAB_MEMBERS) and not user.can(Permission.MANAGE_USERS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an admin can remove a lab admin from a laboratory.",
        )
    return await crud_user.remove_from_laboratory(db, target)


@router.post(
    "/{id}/set-laboratory",
    response_model=UserRead,
    dependencies=[Depends(current_user_manager)],
)
async def set_laboratory(
    id: UUID,
    obj_in: LaboratoryAssignment,
    db: AsyncSession = Depends(get_async_session),
):
    target = await crud_user.get(db, id)
    return await crud_user.set_laboratory(db, target, obj_in.laboratory_id)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user_manager),
):
    if id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account.",
        )
    await user_groups.assert_keeps_an_administrator(db, id)
    await crud_user.delete(db, id)
