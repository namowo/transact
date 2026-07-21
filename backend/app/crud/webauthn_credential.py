from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.crud.exceptions import DatabaseCommitError
from app.models.user import User
from app.models.webauthn_credential import WebAuthnCredential


def _utcnow() -> datetime:
    """Naive UTC now, matching the DB's timezone-naive TIMESTAMP columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class CRUDWebAuthnCredential:
    async def list_for_user(
        self, db: AsyncSession, user: User
    ) -> List[WebAuthnCredential]:
        statement = select(WebAuthnCredential).where(
            WebAuthnCredential.user_id == user.id
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_by_credential_id(
        self, db: AsyncSession, credential_id: str
    ) -> Optional[WebAuthnCredential]:
        statement = select(WebAuthnCredential).where(
            WebAuthnCredential.credential_id == credential_id
        )
        result = await db.execute(statement)
        return result.scalars().first()

    async def create(
        self,
        db: AsyncSession,
        user: User,
        *,
        credential_id: str,
        public_key: bytes,
        sign_count: int,
        device_name: Optional[str] = None,
    ) -> WebAuthnCredential:
        credential = WebAuthnCredential(
            user_id=user.id,
            credential_id=credential_id,
            public_key=public_key,
            sign_count=sign_count,
            device_name=device_name,
        )
        db.add(credential)
        try:
            await db.commit()
            await db.refresh(credential)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return credential

    async def update_sign_count(
        self, db: AsyncSession, credential: WebAuthnCredential, sign_count: int
    ) -> WebAuthnCredential:
        credential.sign_count = sign_count
        credential.last_used_at = _utcnow()
        try:
            await db.commit()
            await db.refresh(credential)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return credential

    async def delete_for_user(
        self, db: AsyncSession, user: User, credential_id: int
    ) -> bool:
        """Delete a credential owned by the given user. Returns False if not found/owned."""
        statement = select(WebAuthnCredential).where(
            WebAuthnCredential.id == credential_id,
            WebAuthnCredential.user_id == user.id,
        )
        result = await db.execute(statement)
        credential = result.scalars().first()
        if credential is None:
            return False

        try:
            await db.delete(credential)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return True


crud_webauthn_credential = CRUDWebAuthnCredential()
