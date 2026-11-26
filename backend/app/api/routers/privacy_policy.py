from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import (
    current_active_user,
    current_optional_user,
    current_site_settings_manager,
    get_async_session,
)
from app.core.permission_catalog import Permission
from app.crud import privacy_policy as crud
from app.models.privacy_policy import PrivacyPolicyVersion
from app.models.user import User
from app.schemas.privacy_policy import (
    PrivacyPolicyAdminRead,
    PrivacyPolicyConsentCreate,
    PrivacyPolicyDraftWrite,
    PrivacyPolicyPublish,
    PrivacyPolicyRead,
)
from app.schemas.user import UserRead
from app.services.mail.messages import send_privacy_policy_updated_mails

router = APIRouter()


def _admin_read(
    policy: PrivacyPolicyVersion, active_id: Optional[int], counts: dict[int, int]
) -> PrivacyPolicyAdminRead:
    if policy.is_draft:
        policy_status = "draft"
    elif policy.id == active_id:
        policy_status = "active"
    else:
        policy_status = "archived"
    return PrivacyPolicyAdminRead.model_validate(
        {
            **PrivacyPolicyRead.model_validate(policy).model_dump(),
            "status": policy_status,
            "created_at": policy.created_at,
            "updated_at": policy.updated_at,
            "created_by": policy.created_by,
            "published_by": policy.published_by,
            "consent_count": counts.get(policy.id, 0),
        }
    )


async def _get_draft_or_404(db: AsyncSession, id: int) -> PrivacyPolicyVersion:
    policy = await crud.get(db, id)
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    if not policy.is_draft:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Published privacy policies can't be changed. Create a new version instead.",
        )
    return policy


@router.get("", response_model=Optional[PrivacyPolicyRead])
async def get_active_privacy_policy(db: AsyncSession = Depends(get_async_session)):
    """The privacy policy in force, or null if none was published yet."""
    return await crud.get_active(db)


@router.get("/versions", response_model=List[PrivacyPolicyAdminRead])
async def list_privacy_policy_versions(
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(current_site_settings_manager),
):
    versions = await crud.list_all(db)
    active = await crud.get_active(db)
    counts = await crud.consent_counts(db)
    return [_admin_read(v, active.id if active else None, counts) for v in versions]


@router.get("/versions/{id}", response_model=PrivacyPolicyRead)
async def get_privacy_policy_version(
    id: int,
    db: AsyncSession = Depends(get_async_session),
    user: Optional[User] = Depends(current_optional_user),
):
    """A published version (anyone, e.g. to read what they agreed to), or
    the draft (admins only)."""
    policy = await crud.get(db, id)
    if policy is None or (
        policy.is_draft
        and not (user and user.can(Permission.MANAGE_SITE_SETTINGS))
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    return policy


@router.post(
    "/versions",
    response_model=PrivacyPolicyAdminRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_privacy_policy_draft(
    obj_in: PrivacyPolicyDraftWrite,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_site_settings_manager),
):
    """Start a new version, prefilled with the active one."""
    try:
        draft = await crud.create_draft(db, user, obj_in)
    except crud.PrivacyPolicyError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return _admin_read(draft, None, {})


@router.patch("/versions/{id}", response_model=PrivacyPolicyAdminRead)
async def update_privacy_policy_draft(
    id: int,
    obj_in: PrivacyPolicyDraftWrite,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(current_site_settings_manager),
):
    draft = await _get_draft_or_404(db, id)
    draft = await crud.update_draft(db, draft, obj_in)
    return _admin_read(draft, None, {})


@router.delete("/versions/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def discard_privacy_policy_draft(
    id: int,
    db: AsyncSession = Depends(get_async_session),
    _: User = Depends(current_site_settings_manager),
):
    draft = await _get_draft_or_404(db, id)
    await crud.delete_draft(db, draft)


@router.post("/versions/{id}/publish", response_model=PrivacyPolicyAdminRead)
async def publish_privacy_policy(
    id: int,
    obj_in: PrivacyPolicyPublish,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_site_settings_manager),
):
    """Make the draft the active policy. From then on it can't be changed,
    and every user has to agree to it before they can continue."""
    draft = await _get_draft_or_404(db, id)
    try:
        policy = await crud.publish(db, draft, user)
    except crud.PrivacyPolicyError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if obj_in.notify_users:
        recipients = [
            (u.email, u.first_name, u.last_name) for u in await crud.users_to_notify(db)
        ]
        background_tasks.add_task(send_privacy_policy_updated_mails, recipients)

    return _admin_read(policy, policy.id, {})


@router.post("/consent", response_model=UserRead)
async def accept_privacy_policy(
    obj_in: PrivacyPolicyConsentCreate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    """The signed-in user agrees to the active privacy policy."""
    active = await crud.get_active(db)
    if active is None or active.id != obj_in.privacy_policy_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The privacy policy has changed in the meantime. Please read the current version.",
        )
    await crud.record_consent(db, user, active)
    return user
