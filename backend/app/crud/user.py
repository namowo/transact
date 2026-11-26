from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.permission_catalog import Permission, SystemGroup
from app.core.security import generate_token, hash_password
from app.crud import user_group as user_groups
from app.crud.base import CRUDBase
from app.crud.exceptions import DatabaseCommitError
from app.models.user import User
from app.schemas.user import UserCreate, UserInvite, UserUpdate


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

    async def record_failed_login(self, db: AsyncSession, user: User) -> User:
        """Count a wrong password; at MAX_FAILED_LOGIN_ATTEMPTS in a row the
        account is locked. Counted in the database, so parallel attempts
        can't slip past the limit."""
        attempts = (
            await db.execute(
                update(User)
                .where(User.id == user.id)
                .values(failed_login_attempts=User.failed_login_attempts + 1)
                .returning(User.failed_login_attempts)
            )
        ).scalar_one()
        limit = settings.MAX_FAILED_LOGIN_ATTEMPTS
        if limit > 0 and attempts >= limit:
            await db.execute(
                update(User)
                .where(User.id == user.id, User.locked_at.is_(None))
                .values(locked_at=datetime.now(timezone.utc).replace(tzinfo=None))
            )
        try:
            await db.commit()
            await db.refresh(user)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))
        return user

    async def reset_failed_logins(self, db: AsyncSession, user: User) -> User:
        if user.failed_login_attempts == 0:
            return user
        user.failed_login_attempts = 0
        try:
            await db.commit()
            await db.refresh(user)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))
        return user

    async def unlock(self, db: AsyncSession, user: User) -> User:
        user.locked_at = None
        user.failed_login_attempts = 0
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

    async def invite(
        self, db: AsyncSession, actor: User, obj_in: UserInvite
    ) -> User:
        """Create the account of an invited user, in the given groups.

        Until they accept, their password is a random one nobody knows. The
        group rules of app.crud.user_group apply; if a group may not be
        assigned, nothing is created."""
        new_user = User(
            email=obj_in.email.lower(),
            hashed_password=hash_password(generate_token()),
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            laboratory_id=obj_in.laboratory_id,
            is_verified=False,
            invitation_pending=True,
        )
        db.add(new_user)
        try:
            await db.flush()
            await db.refresh(new_user, attribute_names=["groups", "laboratory"])
            # Commits.
            await user_groups.set_user_groups(db, actor, new_user, obj_in.group_ids)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))
        except Exception:
            await db.rollback()
            raise

        await db.refresh(new_user)
        return new_user

    async def accept_invitation(
        self, db: AsyncSession, user: User, password: str
    ) -> User:
        """The invited user chose a password - which also proves they own the
        email address."""
        user.hashed_password = hash_password(password)
        user.invitation_pending = False
        user.is_verified = True
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

    async def list_quality_checkers(self, db: AsyncSession) -> List[User]:
        """Who reviews studies submitted for quality check."""
        return await user_groups.list_members_with(db, Permission.QUALITY_CHECK)

    async def administrator_exists(self, db: AsyncSession) -> bool:
        return await user_groups.anyone_has(db, Permission.MANAGE_GROUPS)


crud_user = CRUDUser()
