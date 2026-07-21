from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import (
    assert_manages_laboratory,
    current_active_user,
    current_lab_admin,
    current_superuser,
    get_async_session,
)
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

router = APIRouter()

_crud_user_update = CRUDBase(User)


@router.get(
    "",
    response_model=List[UserRead],
    dependencies=[Depends(current_superuser)],
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


@router.post(
    "/{id}/grant-quality-check",
    response_model=UserRead,
    dependencies=[Depends(current_superuser)],
)
async def grant_quality_check(id: int, db: AsyncSession = Depends(get_async_session)):
    target = await crud_user.get(db, id)
    return await crud_user.set_can_quality_check(db, target, True)


@router.post(
    "/{id}/revoke-quality-check",
    response_model=UserRead,
    dependencies=[Depends(current_superuser)],
)
async def revoke_quality_check(id: int, db: AsyncSession = Depends(get_async_session)):
    target = await crud_user.get(db, id)
    return await crud_user.set_can_quality_check(db, target, False)


@router.post(
    "/{id}/grant-superuser",
    response_model=UserRead,
    dependencies=[Depends(current_superuser)],
)
async def grant_superuser(id: int, db: AsyncSession = Depends(get_async_session)):
    target = await crud_user.get(db, id)
    return await crud_user.set_is_superuser(db, target, True)


@router.post(
    "/{id}/revoke-superuser",
    response_model=UserRead,
    dependencies=[Depends(current_superuser)],
)
async def revoke_superuser(id: int, db: AsyncSession = Depends(get_async_session)):
    target = await crud_user.get(db, id)
    return await crud_user.set_is_superuser(db, target, False)


@router.post("/{id}/grant-lab-admin", response_model=UserRead)
async def grant_lab_admin(
    id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_lab_admin),
):
    target = await crud_user.get(db, id)
    assert_manages_laboratory(user, target.laboratory_id)
    return await crud_user.set_can_manage_lab_users(db, target, True)


@router.post("/{id}/revoke-lab-admin", response_model=UserRead)
async def revoke_lab_admin(
    id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_lab_admin),
):
    target = await crud_user.get(db, id)
    assert_manages_laboratory(user, target.laboratory_id)
    return await crud_user.set_can_manage_lab_users(db, target, False)


@router.post("/{id}/remove-from-laboratory", response_model=UserRead)
async def remove_from_laboratory(
    id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_lab_admin),
):
    target = await crud_user.get(db, id)
    assert_manages_laboratory(user, target.laboratory_id)
    if target.can_manage_lab_users and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an admin can remove a lab admin from a laboratory.",
        )
    return await crud_user.remove_from_laboratory(db, target)


@router.post(
    "/{id}/set-laboratory",
    response_model=UserRead,
    dependencies=[Depends(current_superuser)],
)
async def set_laboratory(
    id: int,
    obj_in: LaboratoryAssignment,
    db: AsyncSession = Depends(get_async_session),
):
    target = await crud_user.get(db, id)
    return await crud_user.set_laboratory(db, target, obj_in.laboratory_id)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    id: int,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_superuser),
):
    if id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account.",
        )
    await crud_user.delete(db, id)
