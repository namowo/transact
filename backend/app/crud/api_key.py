from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import generate_token, hash_token
from app.crud.exceptions import DatabaseCommitError
from app.models.api_key import ApiKey
from app.models.user import User

PREFIX_LENGTH = 8


def _utcnow() -> datetime:
    """Naive UTC now, matching the DB's timezone-naive TIMESTAMP columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class CRUDApiKey:
    async def list_for_user(self, db: AsyncSession, user: User) -> List[ApiKey]:
        statement = select(ApiKey).where(ApiKey.user_id == user.id)
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_by_hash(self, db: AsyncSession, key_hash: str) -> Optional[ApiKey]:
        statement = select(ApiKey).where(ApiKey.key_hash == key_hash)
        result = await db.execute(statement)
        return result.scalars().first()

    async def create(
        self,
        db: AsyncSession,
        user: User,
        *,
        name: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> Tuple[ApiKey, str]:
        token = generate_token()
        api_key = ApiKey(
            user_id=user.id,
            name=name,
            key_hash=hash_token(token),
            prefix=token[:PREFIX_LENGTH],
            expires_at=expires_at,
        )
        db.add(api_key)
        try:
            await db.commit()
            await db.refresh(api_key)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return api_key, token

    async def touch_last_used(self, db: AsyncSession, api_key: ApiKey) -> None:
        api_key.last_used_at = _utcnow()
        try:
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

    async def revoke_for_user(
        self, db: AsyncSession, user: User, api_key_id: UUID
    ) -> bool:
        """Delete an API key owned by the given user. Returns False if not found/owned."""
        statement = select(ApiKey).where(
            ApiKey.id == api_key_id,
            ApiKey.user_id == user.id,
        )
        result = await db.execute(statement)
        api_key = result.scalars().first()
        if api_key is None:
            return False

        try:
            await db.delete(api_key)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return True


crud_api_key = CRUDApiKey()
