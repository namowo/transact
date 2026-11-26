"""A user's second factor: the authenticator app (TOTP) and its recovery
codes. Passkeys live in app.crud.webauthn_credential."""

import enum
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import encryption, totp
from app.crud.exceptions import DatabaseCommitError
from app.models.user import User
from app.models.webauthn_credential import WebAuthnCredential

logger = logging.getLogger(__name__)

# Wrong codes in a row before the code step is locked, and for how long.
MAX_FAILED_ATTEMPTS = 5
LOCKOUT = timedelta(minutes=5)


def _utcnow() -> datetime:
    """Naive UTC now, matching the DB's timezone-naive TIMESTAMP columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class CodeCheck(enum.Enum):
    OK = "ok"
    INVALID = "invalid"
    LOCKED = "locked"


async def _commit(db: AsyncSession, user: User) -> None:
    try:
        await db.commit()
        await db.refresh(user)
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseCommitError(message=str(e))


def _read_secret(user: User, encrypted: str | None) -> str | None:
    """Secrets are stored encrypted (app.core.encryption)."""
    if encrypted is None:
        return None
    try:
        return encryption.decrypt(encrypted)
    except encryption.DecryptionError:
        logger.error(
            "Can't decrypt the authenticator app secret of user %s - did "
            "TWO_FACTOR_ENCRYPTION_KEY (or JWT_SECRET_KEY) change?",
            user.id,
        )
        return None


async def start_totp_setup(db: AsyncSession, user: User) -> str:
    """A new secret for the user to scan; it takes effect once a code from it
    is confirmed (`enable_totp`)."""
    secret = totp.generate_secret()
    user.totp_pending_secret = encryption.encrypt(secret)
    await _commit(db, user)
    return secret


async def enable_totp(db: AsyncSession, user: User, code: str) -> list[str] | None:
    """Turn the authenticator app on if `code` matches the pending secret.
    Returns the new recovery codes (shown once), or None if the code is
    wrong."""
    pending_secret = _read_secret(user, user.totp_pending_secret)
    if pending_secret is None:
        return None
    step = totp.verify(pending_secret, code)
    if step is None:
        return None
    recovery_codes = totp.generate_recovery_codes()
    user.totp_secret = user.totp_pending_secret
    user.totp_pending_secret = None
    user.totp_last_used_step = step
    user.totp_recovery_codes = [totp.hash_recovery_code(c) for c in recovery_codes]
    user.totp_failed_attempts = 0
    user.totp_locked_until = None
    await _commit(db, user)
    return recovery_codes


async def check_code(db: AsyncSession, user: User, code: str) -> CodeCheck:
    """Check a code from the authenticator app, or a recovery code (used up
    when accepted). Too many wrong codes in a row lock the check for a
    while."""
    if user.totp_secret is None:
        return CodeCheck.INVALID
    if user.totp_locked_until is not None and user.totp_locked_until > _utcnow():
        return CodeCheck.LOCKED

    # If the secret can't be decrypted, recovery codes still work.
    secret = _read_secret(user, user.totp_secret)
    step = (
        totp.verify(secret, code, last_used_step=user.totp_last_used_step)
        if secret is not None
        else None
    )
    if step is not None:
        user.totp_last_used_step = step
    else:
        hashed = totp.hash_recovery_code(code)
        if hashed not in (user.totp_recovery_codes or []):
            user.totp_failed_attempts = (user.totp_failed_attempts or 0) + 1
            if user.totp_failed_attempts >= MAX_FAILED_ATTEMPTS:
                user.totp_failed_attempts = 0
                user.totp_locked_until = _utcnow() + LOCKOUT
            await _commit(db, user)
            return CodeCheck.INVALID
        # Reassign so SQLAlchemy sees the JSONB change.
        user.totp_recovery_codes = [c for c in user.totp_recovery_codes if c != hashed]

    user.totp_failed_attempts = 0
    user.totp_locked_until = None
    await _commit(db, user)
    return CodeCheck.OK


async def regenerate_recovery_codes(db: AsyncSession, user: User) -> list[str]:
    recovery_codes = totp.generate_recovery_codes()
    user.totp_recovery_codes = [totp.hash_recovery_code(c) for c in recovery_codes]
    await _commit(db, user)
    return recovery_codes


async def disable_totp(db: AsyncSession, user: User) -> User:
    user.totp_secret = None
    user.totp_pending_secret = None
    user.totp_last_used_step = None
    user.totp_recovery_codes = []
    user.totp_failed_attempts = 0
    user.totp_locked_until = None
    await _commit(db, user)
    return user


async def reset(db: AsyncSession, user: User) -> User:
    """Remove every second factor - the authenticator app and all passkeys -
    for a user who lost them. They set up a new one on their next sign-in."""
    await db.execute(delete(WebAuthnCredential).where(WebAuthnCredential.user_id == user.id))
    return await disable_totp(db, user)
