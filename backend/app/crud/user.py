from typing import List, Optional
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.permission_catalog import Permission, SystemGroup
from app.core.security import hash_password
from app.crud import user_group as user_groups
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
        administrator: bool = False,
    ) -> User:
        new_user = User(
            email=obj_in.email.lower(),
            hashed_password=hash_password(obj_in.password),
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            laboratory_id=obj_in.laboratory_id,
            is_verified=is_verified,
        )
        db.add(new_user)
        if administrator:
            await user_groups.add_to_system_group(db, new_user, SystemGroup.ADMINISTRATOR)
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

    async def set_email(self, db: AsyncSession, user: User, new_email: str) -> User:
        user.email = new_email.lower()
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

    async def dismiss_passkey_prompt(self, db: AsyncSession, user: User) -> User:
        user.passkey_prompt_dismissed = True
        try:
            await db.commit()
            await db.refresh(user)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return user

    async def complete_tour(self, db: AsyncSession, user: User, tour: str) -> User:
        if tour not in (user.completed_tours or []):
            # Reassign rather than append so SQLAlchemy sees the JSONB change.
            user.completed_tours = [*(user.completed_tours or []), tour]
        try:
            await db.commit()
            await db.refresh(user)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return user




    async def remove_from_laboratory(self, db: AsyncSession, user: User) -> User:
        user.laboratory_id = None
        await user_groups.leave_laboratory_groups(db, user)
        try:
            await db.commit()
            await db.refresh(user)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return user

    async def set_laboratory(
        self, db: AsyncSession, user: User, laboratory_id: Optional[UUID]
    ) -> User:
        if laboratory_id != user.laboratory_id:
            await user_groups.leave_laboratory_groups(db, user)
        user.laboratory_id = laboratory_id
        try:
            await db.commit()
            await db.refresh(user)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return user

    async def list_by_laboratory(
        self, db: AsyncSession, laboratory_id: UUID
    ) -> List[User]:
        statement = select(self.model).where(
            self.model.laboratory_id == laboratory_id
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def list_all(self, db: AsyncSession) -> List[User]:
        statement = select(self.model)
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def list_laboratory_managers(self, db: AsyncSession) -> List[User]:
        """Who reviews requests for new laboratories."""
        return await user_groups.list_members_with(db, Permission.MANAGE_LABORATORIES)

    async def administrator_exists(self, db: AsyncSession) -> bool:
        return await user_groups.anyone_has(db, Permission.MANAGE_GROUPS)


crud_user = CRUDUser()
