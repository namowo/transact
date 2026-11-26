from datetime import timedelta
from typing import Union

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.users import ACCEPT_INVITATION_PURPOSE
from app.core.config import settings
from app.core.deps import get_async_session
from app.core.security import (
    create_access_token,
    create_two_factor_login_token,
    decode_two_factor_login_token,
    verify_password,
)
from app.crud import privacy_policy as crud_privacy_policy
from app.crud import two_factor
from app.crud.laboratory import crud_laboratory
from app.crud.user import crud_user
from app.crud.user_token import crud_user_token
from app.crud.webauthn_credential import crud_webauthn_credential
from app.models.user import User
from app.schemas.auth import (
    AuthConfig,
    EmailVerificationConfirm,
    InvitationAccept,
    PasswordResetConfirm,
    PasswordResetRequest,
    ResendVerificationRequest,
    TwoFactorChallenge,
    TwoFactorLogin,
)
from app.schemas.laboratory import LaboratoryCreate
from app.schemas.user import SetupStatus, SuperuserSetup, UserCreate, UserRead
from app.services.mail.messages import (
    send_reset_password_mail,
    send_verification_mail,
    send_welcome_mail,
)

router = APIRouter()

VERIFY_EMAIL_PURPOSE = "verify_email"
RESET_PASSWORD_PURPOSE = "reset_password"


def set_session_cookie(response: Response, user: User, *, mfa: bool = False) -> None:
    """Issue a JWT session cookie for the given user. Shared by password and
    passkey login so both end up in the same authenticated session.

    `mfa`: the sign-in used a second factor. Without one, while two-factor
    authentication is required, the session may only set one up - and is
    marked so on the returned user. (Sessions without a second factor are
    only issued to users who have none.)"""
    access_token = create_access_token(subject=str(user.id), mfa=mfa)
    if not mfa and settings.TWO_FACTOR_REQUIRED:
        user.two_factor_setup_required = True
    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=access_token,
        max_age=settings.VITE_JWT_LIFETIME_SECONDS,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )

GENERIC_ACCEPTED_MESSAGE = {
    "message": "If an account matches this address, an email has been sent."
}


REGISTRATION_DISABLED = "Registration is disabled on this instance."
INVITATIONS_DISABLED = "Invitations are disabled on this instance."
INVALID_CODE = "This code is invalid. Please try again."
CODE_LOCKED = "Too many wrong codes. Please wait a few minutes and try again."
ACCOUNT_LOCKED = (
    "This account is locked after too many failed sign-in attempts. "
    "Please contact an administrator to unlock it."
)


def assert_not_locked(user: User) -> None:
    if user.is_locked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=ACCOUNT_LOCKED)


@router.get("/config", response_model=AuthConfig)
async def auth_config():
    return AuthConfig(
        registration_enabled=settings.REGISTRATION_ENABLED,
        invitations_enabled=settings.INVITATIONS_ENABLED,
        two_factor_required=settings.TWO_FACTOR_REQUIRED,
    )


@router.get("/setup-status", response_model=SetupStatus)
async def setup_status(db: AsyncSession = Depends(get_async_session)):
    return SetupStatus(needs_setup=not await crud_user.administrator_exists(db))


@router.post("/setup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def setup(
    response: Response,
    obj_in: SuperuserSetup,
    db: AsyncSession = Depends(get_async_session),
):
    if await crud_user.administrator_exists(db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Setup has already been completed.",
        )

    laboratory = await crud_laboratory.create(
        db,
        LaboratoryCreate(
            laboratory_name=f"{obj_in.first_name} {obj_in.last_name}",
            institutional_affiliation=f"{obj_in.first_name} {obj_in.last_name}",
            city="",
            country="",
            email=obj_in.email,
        ),
    )

    user = await crud_user.create(
        db,
        UserCreate(
            email=obj_in.email,
            password=obj_in.password,
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            laboratory_id=laboratory.id,
        ),
        is_verified=True,
        administrator=True,
    )

    set_session_cookie(response, user)
    return user


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    obj_in: UserCreate, db: AsyncSession = Depends(get_async_session)
):
    if not settings.REGISTRATION_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=REGISTRATION_DISABLED
        )
    if await crud_user.get_by_email(db, obj_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    active_policy = await crud_privacy_policy.get_active(db)
    if active_policy is not None and obj_in.privacy_policy_id != active_policy.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The privacy policy has changed in the meantime. Please reload the page and read the current version.",
        )

    # New users join a laboratory through a membership request, which the
    # laboratory's admins approve - never directly on sign-up.
    user = await crud_user.create(db, obj_in.model_copy(update={"laboratory_id": None}))
    if active_policy is not None:
        await crud_privacy_policy.record_consent(db, user, active_policy)

    await send_welcome_mail(user)
    token = await crud_user_token.create(
        db,
        user,
        VERIFY_EMAIL_PURPOSE,
        timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS),
    )
    await send_verification_mail(user, token)

    return user


@router.post("/login", response_model=Union[UserRead, TwoFactorChallenge])
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_session),
):
    user = await crud_user.get_by_email(db, form_data.username)
    if user is not None:
        # Even with the right password: no more guessing once locked.
        assert_not_locked(user)
    if user is None or not verify_password(form_data.password, user.hashed_password):
        if user is not None:
            user = await crud_user.record_failed_login(db, user)
            assert_not_locked(user)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    user = await crud_user.reset_failed_logins(db, user)

    has_passkey = await crud_webauthn_credential.exists_for_user(db, user)
    if user.totp_enabled:
        return TwoFactorChallenge(
            login_token=create_two_factor_login_token(str(user.id)),
            methods=["totp", "passkey"] if has_passkey else ["totp"],
        )
    if settings.TWO_FACTOR_REQUIRED and has_passkey:
        # The passkey is their second factor; a password alone may not even
        # open a session to set up another one.
        return TwoFactorChallenge(methods=["passkey"])

    set_session_cookie(response, user)
    return user


@router.post("/login/two-factor", response_model=UserRead)
async def login_two_factor(
    response: Response,
    obj_in: TwoFactorLogin,
    db: AsyncSession = Depends(get_async_session),
):
    """Finish a password sign-in with a code from the authenticator app or a
    recovery code."""
    user_id = decode_two_factor_login_token(obj_in.login_token)
    user = await crud_user.get(db, user_id) if user_id else None
    if user is None or not user.is_active or not user.totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This sign-in has expired. Please log in again.",
        )
    assert_not_locked(user)

    result = await two_factor.check_code(db, user, obj_in.code)
    if result is two_factor.CodeCheck.LOCKED:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=CODE_LOCKED)
    if result is not two_factor.CodeCheck.OK:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=INVALID_CODE)

    set_session_cookie(response, user, mfa=True)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie(key=settings.ACCESS_TOKEN_COOKIE_NAME, path="/")


@router.post("/verify-email")
async def verify_email(
    obj_in: EmailVerificationConfirm, db: AsyncSession = Depends(get_async_session)
):
    user = await crud_user_token.get_valid_user(
        db, obj_in.token, VERIFY_EMAIL_PURPOSE
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This verification link is invalid or has expired.",
        )

    await crud_user.set_verified(db, user)
    return {"message": "Email address confirmed. You can now log in."}


@router.post("/resend-verification", status_code=status.HTTP_202_ACCEPTED)
async def resend_verification(
    obj_in: ResendVerificationRequest, db: AsyncSession = Depends(get_async_session)
):
    user = await crud_user.get_by_email(db, obj_in.email)
    if user is not None and not user.is_verified:
        token = await crud_user_token.create(
            db,
            user,
            VERIFY_EMAIL_PURPOSE,
            timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS),
        )
        await send_verification_mail(user, token)

    return GENERIC_ACCEPTED_MESSAGE


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    obj_in: PasswordResetRequest, db: AsyncSession = Depends(get_async_session)
):
    user = await crud_user.get_by_email(db, obj_in.email)
    if user is not None:
        token = await crud_user_token.create(
            db,
            user,
            RESET_PASSWORD_PURPOSE,
            timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS),
        )
        await send_reset_password_mail(user, token)

    return GENERIC_ACCEPTED_MESSAGE


@router.post("/reset-password")
async def reset_password(
    obj_in: PasswordResetConfirm, db: AsyncSession = Depends(get_async_session)
):
    user = await crud_user_token.get_valid_user(
        db, obj_in.token, RESET_PASSWORD_PURPOSE
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid or has expired.",
        )

    if user.invitation_pending:
        # The reset link proves they own the address, just like the
        # invitation link would.
        await crud_user.accept_invitation(db, user, obj_in.new_password)
    else:
        await crud_user.set_password(db, user, obj_in.new_password)
    return {"message": "Password updated. You can now log in with your new password."}


@router.post("/accept-invitation", response_model=UserRead)
async def accept_invitation(
    response: Response,
    obj_in: InvitationAccept,
    db: AsyncSession = Depends(get_async_session),
):
    if not settings.INVITATIONS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=INVITATIONS_DISABLED
        )
    user = await crud_user_token.get_valid_user(
        db, obj_in.token, ACCEPT_INVITATION_PURPOSE
    )
    if user is None or not user.invitation_pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation link is invalid or has expired.",
        )

    user = await crud_user.accept_invitation(db, user, obj_in.password)
    set_session_cookie(response, user)
    return user
