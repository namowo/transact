from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import generate_token, hash_token
from app.crud.exceptions import DatabaseCommitError
from app.models.user import User
from app.models.user_token import UserToken


def _utcnow() -> datetime:
    """Naive UTC now, matching the DB's timezone-naive TIMESTAMP columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class CRUDUserToken:
    async def create(
        self, db: AsyncSession, user: User, purpose: str, expires_in: timedelta
    ) -> str:
        """Create a new token for the user, invalidating any existing ones
        for the same purpose, and return the raw (unhashed) token."""
        await db.execute(
            delete(UserToken).where(
                UserToken.user_id == user.id, UserToken.purpose == purpose
            )
        )

        raw_token = generate_token()
        db.add(
            UserToken(
                user_id=user.id,
                token_hash=hash_token(raw_token),
                purpose=purpose,
                expires_at=_utcnow() + expires_in,
            )
        )
        try:
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return raw_token

    async def get_valid_user(
        self, db: AsyncSession, raw_token: str, purpose: str
    ) -> Optional[User]:
        statement = select(UserToken).where(
            UserToken.token_hash == hash_token(raw_token),
            UserToken.purpose == purpose,
        )
        result = await db.execute(statement)
        token = result.scalars().first()

        if token is None:
            return None

        if token.expires_at < _utcnow():
            await db.delete(token)
            await db.commit()
            return None

        user = await db.get(User, token.user_id)

        await db.delete(token)
        try:
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return user


crud_user_token = CRUDUserToken()
