from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_async_session
from app.core.security import create_access_token, verify_password
from app.crud.laboratory import crud_laboratory
from app.crud.user import crud_user
from app.crud.user_token import crud_user_token
from app.models.user import User
from app.schemas.auth import (
    EmailVerificationConfirm,
    PasswordResetConfirm,
    PasswordResetRequest,
    ResendVerificationRequest,
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


def set_session_cookie(response: Response, user: User) -> None:
    """Issue a JWT session cookie for the given user. Shared by password and
    passkey login so both end up in the same authenticated session."""
    access_token = create_access_token(subject=str(user.id))
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


@router.get("/setup-status", response_model=SetupStatus)
async def setup_status(db: AsyncSession = Depends(get_async_session)):
    return SetupStatus(needs_setup=not await crud_user.superuser_exists(db))


@router.post("/setup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def setup(
    response: Response,
    obj_in: SuperuserSetup,
    db: AsyncSession = Depends(get_async_session),
):
    if await crud_user.superuser_exists(db):
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
        is_superuser=True,
    )

    set_session_cookie(response, user)
    return user


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    obj_in: UserCreate, db: AsyncSession = Depends(get_async_session)
):
    if await crud_user.get_by_email(db, obj_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    user = await crud_user.create(db, obj_in)

    await send_welcome_mail(user)
    token = await crud_user_token.create(
        db,
        user,
        VERIFY_EMAIL_PURPOSE,
        timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS),
    )
    await send_verification_mail(user, token)

    return user


@router.post("/login", response_model=UserRead)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_session),
):
    user = await crud_user.get_by_email(db, form_data.username)
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    set_session_cookie(response, user)
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

    await crud_user.set_password(db, user, obj_in.new_password)
    return {"message": "Password updated. You can now log in with your new password."}
