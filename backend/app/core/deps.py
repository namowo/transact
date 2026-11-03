from datetime import datetime, timezone
from typing import AsyncGenerator, Optional
from uuid import UUID

import jwt
from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import SessionLocal, async_session_maker
from app.core.security import decode_access_token, hash_token
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


async def current_superuser(user: User = Depends(current_active_user)) -> User:
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return user


async def current_quality_checker(user: User = Depends(current_active_user)) -> User:
    if not (user.is_superuser or user.can_quality_check):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return user


async def current_lab_admin(user: User = Depends(current_active_user)) -> User:
    if not (user.is_superuser or user.can_manage_lab_users):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return user


def assert_manages_laboratory(user: User, laboratory_id: Optional[int]) -> None:
    """Raise 403 unless `user` is a superuser or is the lab admin of `laboratory_id`."""
    if user.is_superuser:
        return
    if user.can_manage_lab_users and user.laboratory_id == laboratory_id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can only manage users in your own laboratory.",
    )


# Alias kept for readability where "any authenticated user" is meant.
current_user = get_current_user
