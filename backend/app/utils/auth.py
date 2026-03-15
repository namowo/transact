import contextlib

# from __future__ import annotations
from fastapi_users.exceptions import UserAlreadyExists

from app.core.deps import get_async_session, get_user_db, get_user_manager
from app.models.user import User
from app.schemas.user import UserCreate
from app.crud.exceptions import AuthorizationError


def satzung_permissions(user: User) -> dict:

    filters = {"satzung_id__isnot": True}  # Default: only non-null `satzung_id`

    if not (user and user.is_superuser):
        filters["published"] = True  # Normal users see only published Satzungen

    return filters


def check_user_auth(user: User, superuser_required: bool = False) -> bool:
    """
    Check if a user is authorized to access a specific municipality.

    :param user: The user instance to check.
    :param municipality_id: The ID of the municipality to access.
    :raises AuthorizationError: If the user is not authorized to access the resource.
    """
    grant_access = True

    if superuser_required:
        if not user.is_superuser:
            grant_access = False

    if not grant_access:
        raise AuthorizationError(
            detail="User is not authorized to access this resource"
        )


get_async_session_context = contextlib.asynccontextmanager(get_async_session)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


async def create_user(user: UserCreate) -> User:
    try:
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    user_created = await user_manager.create(user)
                    print(f"User created {user_created}")
                    return user_created
    except UserAlreadyExists:
        print(f"User {user.email} already exists")
        raise
