from datetime import datetime, timezone
from typing import AsyncGenerator, Optional
from uuid import UUID

import jwt
from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import SessionLocal, async_session_maker
from app.core.security import decode_access_token, hash_token
from app.core.permission_catalog import Permission
from app.crud.api_key import crud_api_key
from app.models.user import User


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
)


async def _resolve_user(
    token: Optional[str], db: AsyncSession
) -> Optional[User]:
    if token is None:
        return None
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
    except jwt.PyJWTError:
        return None
    if user_id is None:
        return None
    try:
        return await db.get(User, UUID(user_id))
    except ValueError:
        return None


def _cookie_token(
    access_token: Optional[str] = Cookie(
        default=None, alias=settings.ACCESS_TOKEN_COOKIE_NAME
    ),
) -> Optional[str]:
    return access_token


def _bearer_token(
    authorization: Optional[str] = Header(default=None),
) -> Optional[str]:
    if authorization is None:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


async def _resolve_user_from_api_key(
    token: Optional[str], db: AsyncSession
) -> Optional[User]:
    if token is None:
        return None
    api_key = await crud_api_key.get_by_hash(db, hash_token(token))
    if api_key is None:
        return None
    if api_key.expires_at is not None:
        expires_at = api_key.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            return None
    await crud_api_key.touch_last_used(db, api_key)
    return await db.get(User, api_key.user_id)


async def get_current_user(
    cookie_token: Optional[str] = Depends(_cookie_token),
    bearer_token: Optional[str] = Depends(_bearer_token),
    db: AsyncSession = Depends(get_async_session),
) -> User:
    user = await _resolve_user(cookie_token, db)
    if user is None:
        user = await _resolve_user_from_api_key(bearer_token, db)
    if user is None:
        raise credentials_exception
    return user


async def current_optional_user(
    cookie_token: Optional[str] = Depends(_cookie_token),
    bearer_token: Optional[str] = Depends(_bearer_token),
    db: AsyncSession = Depends(get_async_session),
) -> Optional[User]:
    user = await _resolve_user(cookie_token, db)
    if user is None:
        user = await _resolve_user_from_api_key(bearer_token, db)
    return user


async def current_active_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user


def require(*permissions: Permission):
    """Dependency returning the active user if they hold any of `permissions`.

    Laboratory-scoped permissions only say the user may act within their own
    laboratory; endpoints still have to check which laboratory is affected
    (see app.core.permissions)."""

    async def dependency(user: User = Depends(current_active_user)) -> User:
        if not any(user.can(permission) for permission in permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges",
            )
        return user

    return dependency


current_user_manager = require(Permission.MANAGE_USERS)
current_laboratory_manager = require(Permission.MANAGE_LABORATORIES)
current_quality_checker = require(Permission.QUALITY_CHECK)
current_catalog_editor = require(Permission.EDIT_CATALOG)
current_catalog_deleter = require(Permission.DELETE_CATALOG)
current_method_manager = require(Permission.MANAGE_METHODS)
current_site_settings_manager = require(Permission.MANAGE_SITE_SETTINGS)
# Study data is further restricted per study by app.core.permissions.
current_data_editor = require(
    Permission.ENTER_DATA, Permission.EDIT_ALL_LABORATORY_DATA
)
# Anyone who manages users: of every laboratory, or of their own.
current_member_manager = require(
    Permission.MANAGE_USERS, Permission.MANAGE_LAB_MEMBERS
)


def manages_laboratory_members(user: User, laboratory_id: Optional[UUID]) -> bool:
    return user.can(Permission.MANAGE_USERS) or user.can_in_laboratory(
        Permission.MANAGE_LAB_MEMBERS, laboratory_id
    )


def assert_manages_laboratory(user: User, laboratory_id: Optional[UUID]) -> None:
    """Raise 403 unless `user` manages the members of `laboratory_id`."""
    if not manages_laboratory_members(user, laboratory_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage users in your own laboratory.",
        )


# Alias kept for readability where "any authenticated user" is meant.
current_user = get_current_user
