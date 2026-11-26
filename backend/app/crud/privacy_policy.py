from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.privacy_policy import PrivacyPolicyConsent, PrivacyPolicyVersion
from app.models.user import User
from app.schemas.privacy_policy import PrivacyPolicyDraftWrite


class PrivacyPolicyError(Exception):
    pass


async def get(db: AsyncSession, id: int) -> Optional[PrivacyPolicyVersion]:
    return await db.get(PrivacyPolicyVersion, id)


async def get_active(db: AsyncSession) -> Optional[PrivacyPolicyVersion]:
    """The most recently published version, if any."""
    result = await db.execute(
        select(PrivacyPolicyVersion)
        .where(PrivacyPolicyVersion.version.is_not(None))
        .order_by(PrivacyPolicyVersion.version.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_draft(db: AsyncSession) -> Optional[PrivacyPolicyVersion]:
    result = await db.execute(
        select(PrivacyPolicyVersion).where(PrivacyPolicyVersion.published_at.is_(None))
    )
    return result.scalar_one_or_none()


async def list_all(db: AsyncSession) -> list[PrivacyPolicyVersion]:
    """Every version, the draft first, then newest to oldest."""
    result = await db.execute(
        select(PrivacyPolicyVersion).order_by(
            PrivacyPolicyVersion.version.desc().nulls_first()
        )
    )
    return list(result.scalars().all())


async def consent_counts(db: AsyncSession) -> dict[int, int]:
    result = await db.execute(
        select(
            PrivacyPolicyConsent.policy_version_id, func.count(PrivacyPolicyConsent.id)
        ).group_by(PrivacyPolicyConsent.policy_version_id)
    )
    return dict(result.all())


async def create_draft(
    db: AsyncSession, user: User, obj_in: PrivacyPolicyDraftWrite
) -> PrivacyPolicyVersion:
    if await get_draft(db) is not None:
        raise PrivacyPolicyError(
            "There already is a draft. Edit or discard it first."
        )
    # Start from the active policy, so admins only change what changed.
    active = await get_active(db)
    draft = PrivacyPolicyVersion(
        mode=active.mode if active else "text",
        text=active.text if active else None,
        url=active.url if active else None,
        created_by_id=user.id,
    )
    for field, value in obj_in.model_dump(exclude_unset=True).items():
        setattr(draft, field, value)
    db.add(draft)
    await db.commit()
    await db.refresh(draft)
    return draft


def _assert_draft(policy: PrivacyPolicyVersion) -> None:
    if not policy.is_draft:
        raise PrivacyPolicyError(
            "Published privacy policies can't be changed. Create a new version instead."
        )


async def update_draft(
    db: AsyncSession, policy: PrivacyPolicyVersion, obj_in: PrivacyPolicyDraftWrite
) -> PrivacyPolicyVersion:
    _assert_draft(policy)
    for field, value in obj_in.model_dump(exclude_unset=True).items():
        setattr(policy, field, value)
    policy.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()
    await db.refresh(policy)
    return policy


async def delete_draft(db: AsyncSession, policy: PrivacyPolicyVersion) -> None:
    _assert_draft(policy)
    await db.delete(policy)
    await db.commit()


async def publish(
    db: AsyncSession, policy: PrivacyPolicyVersion, user: User
) -> PrivacyPolicyVersion:
    _assert_draft(policy)
    if policy.mode == "url" and not (policy.url or "").strip():
        raise PrivacyPolicyError("Enter the link to the privacy policy.")
    if policy.mode == "text" and not (policy.text or "").strip():
        raise PrivacyPolicyError("Enter the text of the privacy policy.")

    latest = await db.scalar(select(func.max(PrivacyPolicyVersion.version)))
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    policy.version = (latest or 0) + 1
    policy.published_at = now
    policy.published_by_id = user.id
    policy.updated_at = now
    await db.commit()
    await db.refresh(policy)
    return policy


async def record_consent(
    db: AsyncSession, user: User, policy: PrivacyPolicyVersion
) -> None:
    exists = await db.scalar(
        select(PrivacyPolicyConsent.id).where(
            PrivacyPolicyConsent.user_id == user.id,
            PrivacyPolicyConsent.policy_version_id == policy.id,
        )
    )
    if exists is None:
        db.add(PrivacyPolicyConsent(user_id=user.id, policy_version_id=policy.id))
        await db.commit()
    await db.refresh(user)
    await db.refresh(user, ["privacy_policy_consents"])


async def users_to_notify(db: AsyncSession) -> list[User]:
    """Everyone who can sign in."""
    result = await db.execute(
        select(User).where(
            User.is_active.is_(True),
            User.is_verified.is_(True),
            User.invitation_pending.is_(False),
        )
    )
    return list(result.scalars().all())
