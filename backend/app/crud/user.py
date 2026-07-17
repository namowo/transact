from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import hash_password
from app.crud.base import CRUDBase
from app.crud.exceptions import DatabaseCommitError
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        statement = select(self.model).where(self.model.email == email.lower())
        result = await db.execute(statement)
        return result.scalars().first()

    async def create(
        self,
        db: AsyncSession,
        obj_in: UserCreate,
        *,
        is_verified: bool = False,
        is_superuser: bool = False,
    ) -> User:
        new_user = User(
            email=obj_in.email.lower(),
            hashed_password=hash_password(obj_in.password),
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            laboratory_id=obj_in.laboratory_id,
            is_verified=is_verified,
            is_superuser=is_superuser,
        )
        db.add(new_user)
        try:
            await db.commit()
            await db.refresh(new_user)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return new_user

    async def set_password(
        self, db: AsyncSession, user: User, new_password: str
    ) -> User:
        user.hashed_password = hash_password(new_password)
        try:
            await db.commit()
            await db.refresh(user)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return user

    async def set_verified(self, db: AsyncSession, user: User) -> User:
        user.is_verified = True
        try:
            await db.commit()
            await db.refresh(user)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return user


crud_user = CRUDUser()
