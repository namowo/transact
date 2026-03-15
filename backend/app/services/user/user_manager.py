from typing import Optional

from datetime import datetime, timedelta, timezone
from fastapi import Request
from fastapi_users import BaseUserManager, UUIDIDMixin
from uuid import UUID

from app.models.user import User
from app.core.config import settings
from app.services.mail.messages import (
    send_welcome_mail,
    send_reset_password_mail,
    send_verification_mail,
)


class UserManager(UUIDIDMixin, BaseUserManager[User, UUID]):
    reset_password_token_secret = settings.RESET_PASSWORD_TOKEN_SECRET
    verification_token_secret = settings.VERIFICATION_TOKEN_SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

        await send_welcome_mail(user)

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

        await send_reset_password_mail(user, token)

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")

        await send_verification_mail(user, token)

    async def on_after_verify(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has been verified")
