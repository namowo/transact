from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.crud.exceptions import DatabaseCommitError
from app.models.user import User
from app.models.webauthn_challenge import WebAuthnChallenge


def _utcnow() -> datetime:
    """Naive UTC now, matching the DB's timezone-naive TIMESTAMP columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class CRUDWebAuthnChallenge:
    async def store(
        self, db: AsyncSession, user: User, purpose: str, raw_challenge: str, expires_in: timedelta
    ) -> None:
        """Persist a challenge value already generated elsewhere (e.g. by the
        webauthn library), invalidating any existing challenge for the same
        purpose."""
        await db.execute(
            delete(WebAuthnChallenge).where(
                WebAuthnChallenge.user_id == user.id,
                WebAuthnChallenge.purpose == purpose,
            )
        )

        db.add(
            WebAuthnChallenge(
                user_id=user.id,
                challenge=raw_challenge,
                purpose=purpose,
                expires_at=_utcnow() + expires_in,
            )
        )
        try:
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

    async def get_valid(
        self, db: AsyncSession, user: User, purpose: str
    ) -> Optional[str]:
        """Fetch and consume the current challenge for a user/purpose, or
        None if missing/expired."""
        statement = select(WebAuthnChallenge).where(
            WebAuthnChallenge.user_id == user.id,
            WebAuthnChallenge.purpose == purpose,
        )
        result = await db.execute(statement)
        challenge = result.scalars().first()

        if challenge is None:
            return None

        if challenge.expires_at < _utcnow():
            await db.delete(challenge)
            await db.commit()
            return None

        raw_challenge = challenge.challenge

        await db.delete(challenge)
        try:
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return raw_challenge


crud_webauthn_challenge = CRUDWebAuthnChallenge()
