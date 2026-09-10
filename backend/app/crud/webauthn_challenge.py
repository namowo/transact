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
        self,
        db: AsyncSession,
        user: Optional[User],
        purpose: str,
        raw_challenge: str,
        expires_in: timedelta,
    ) -> None:
        """Persist a challenge value already generated elsewhere (e.g. by the
        webauthn library). ``user`` is None for a usernameless login
        challenge, where the user isn't known until the assertion comes
        back; since anonymous challenges aren't scoped to one identity, an
        old one is left to expire on its own TTL rather than invalidated
        here, so concurrent anonymous logins from different people don't
        invalidate each other."""
        if user:
            await db.execute(
                delete(WebAuthnChallenge).where(
                    WebAuthnChallenge.user_id == user.id,
                    WebAuthnChallenge.purpose == purpose,
                )
            )

        db.add(
            WebAuthnChallenge(
                user_id=user.id if user else None,
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
        return await self._consume(db, statement)

    async def get_valid_anonymous(
        self, db: AsyncSession, raw_challenge: str, purpose: str
    ) -> bool:
        """Fetch and consume a usernameless (no user_id) challenge by its
        value. Returns whether a matching, unexpired challenge existed."""
        statement = select(WebAuthnChallenge).where(
            WebAuthnChallenge.user_id.is_(None),
            WebAuthnChallenge.purpose == purpose,
            WebAuthnChallenge.challenge == raw_challenge,
        )
        return await self._consume(db, statement) is not None

    async def _consume(
        self, db: AsyncSession, statement
    ) -> Optional[str]:
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
