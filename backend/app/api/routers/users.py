from datetime import timedelta
from typing import List, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.notification_catalog import NOTIFICATION_TYPES, NotificationType
from app.core.deps import (
    assert_manages_laboratory,
    current_active_user,
    current_member_manager,
    current_session_user,
    current_user_manager,
    get_async_session,
)
from app.core.permission_catalog import Permission
from app.crud import two_factor
from app.crud import user_group as user_groups
from app.core.security import verify_password
from app.crud.base import CRUDBase
from app.crud.user import crud_user
from app.crud.user_token import crud_user_token
from app.models.user import User
from app.schemas.user import (
    EmailChange,
    LaboratoryAssignment,
    PasswordChange,
    UserInvite,
    UserRead,
    NotificationTypeRead,
    UserUpdate,
)
from app.schemas.user_group import UserGroupAssignment
from app.services.mail.messages import send_invitation_mail

ACCEPT_INVITATION_PURPOSE = "accept_invitation"

router = APIRouter()


def assert_invitations_enabled() -> None:
    if not settings.INVITATIONS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invitations are disabled on this instance.",
        )


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


async def _send_invitation(db: AsyncSession, target: User, inviter: User) -> None:
    token = await crud_user_token.create(
        db,
        target,
        ACCEPT_INVITATION_PURPOSE,
        timedelta(hours=settings.INVITATION_TOKEN_EXPIRE_HOURS),
    )
    await send_invitation_mail(target, inviter, token)


@router.post("/invite", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def invite_user(
    obj_in: UserInvite,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_member_manager),
):
    """Create an account for someone and email them a link to choose their
    password. Admins invite to any laboratory (or none); lab admins to their
    own."""
    assert_invitations_enabled()
    if not user.can(Permission.MANAGE_USERS):
        obj_in = obj_in.model_copy(
            update={"laboratory_id": obj_in.laboratory_id or user.laboratory_id}
        )
        assert_manages_laboratory(user, obj_in.laboratory_id)
    if await crud_user.get_by_email(db, obj_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    target = await crud_user.invite(db, user, obj_in)
    await _send_invitation(db, target, user)
    return target


@router.post("/{id}/resend-invitation", response_model=UserRead)
async def resend_invitation(
    id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_member_manager),
):
    assert_invitations_enabled()
    target = await crud_user.get(db, id)
    assert_manages_laboratory_or_users(user, target)
    if not target.invitation_pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user has already accepted their invitation.",
        )
    await _send_invitation(db, target, user)
    return target


@router.get("/me", response_model=UserRead)
async def read_me(user: User = Depends(current_session_user)):
    # Also answers while the user still has to set up a second factor
    # (`two_factor_setup_required`), so the frontend can send them there.
    return user


@router.patch("/me", response_model=UserRead)
async def update_me(
    obj_in: UserUpdate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    if obj_in.notification_settings is not None:
        # Merge, so changing one switch keeps the others. A new dict, so the
        # JSONB change is detected.
        # Types no longer in the catalog are dropped.
        known = {t.value for t in NotificationType}
        merged = {
            NotificationType(type): dict(channels)
            for type, channels in (user.notification_settings or {}).items()
            if type in known
        }
        for type, channels in obj_in.notification_settings.items():
            merged.setdefault(type, {}).update(channels)
        obj_in = obj_in.model_copy(update={"notification_settings": merged})
    return await _crud_user_update.update(db, user.id, obj_in)


@router.get("/me/notification-types", response_model=List[NotificationTypeRead])
async def list_my_notification_types(user: User = Depends(current_active_user)):
    """The notifications the user's permissions let them receive."""
    return [
        NotificationTypeRead(
            key=info.key.value,
            label=info.label,
            description=info.description,
            channels=list(info.defaults),
        )
        for info in NOTIFICATION_TYPES
        if user.can_receive_notification(info.key)
    ]


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
    "/{id}/unlock",
    response_model=UserRead,
    dependencies=[Depends(current_user_manager)],
)
async def unlock_user(id: UUID, db: AsyncSession = Depends(get_async_session)):
    """Let a user sign in again after their account was locked for too many
    wrong passwords."""
    target = await crud_user.get(db, id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return await crud_user.unlock(db, target)


@router.post(
    "/{id}/reset-two-factor",
    response_model=UserRead,
    dependencies=[Depends(current_user_manager)],
)
async def reset_two_factor(id: UUID, db: AsyncSession = Depends(get_async_session)):
    """Remove the user's authenticator app and passkeys, for when they lost
    them. If two-factor authentication is required, they set up a new
    second factor after signing in with their password."""
    target = await crud_user.get(db, id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return await two_factor.reset(db, target)


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
    user: User = Depends(current_member_manager),
):
    """Admins delete any account; lab admins may only withdraw pending
    invitations to their laboratory."""
    if not user.can(Permission.MANAGE_USERS):
        target = await crud_user.get(db, id)
        if not target.invitation_pending:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only withdraw pending invitations.",
            )
        assert_manages_laboratory(user, target.laboratory_id)
    if id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account.",
        )
    await user_groups.assert_keeps_an_administrator(db, id)
    await crud_user.delete(db, id)
