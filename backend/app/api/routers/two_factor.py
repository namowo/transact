"""Managing one's own authenticator app (TOTP) and recovery codes."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routers.auth import CODE_LOCKED, INVALID_CODE, set_session_cookie
from app.core import totp
from app.core.config import settings
from app.core.deps import current_active_user, current_session_user, get_async_session
from app.core.security import verify_password
from app.crud import two_factor
from app.crud.webauthn_credential import crud_webauthn_credential
from app.models.user import User
from app.schemas.auth import RecoveryCodes, TotpCode, TotpDisable, TotpSetup

router = APIRouter()


async def _require_code(db: AsyncSession, user: User, code: str) -> None:
    result = await two_factor.check_code(db, user, code)
    if result is two_factor.CodeCheck.LOCKED:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=CODE_LOCKED)
    if result is not two_factor.CodeCheck.OK:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=INVALID_CODE)


@router.post("/totp/setup", response_model=TotpSetup)
async def totp_setup(
    user: User = Depends(current_session_user),
    db: AsyncSession = Depends(get_async_session),
):
    """A new secret for the authenticator app. It takes effect once a code
    from it is confirmed at /totp/enable."""
    if user.totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The authenticator app is already set up.",
        )
    secret = await two_factor.start_totp_setup(db, user)
    return TotpSetup(
        secret=secret,
        provisioning_uri=totp.provisioning_uri(secret, user.email, settings.TOTP_ISSUER),
    )


@router.post("/totp/enable", response_model=RecoveryCodes)
async def totp_enable(
    obj_in: TotpCode,
    response: Response,
    user: User = Depends(current_session_user),
    db: AsyncSession = Depends(get_async_session),
):
    if user.totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The authenticator app is already set up.",
        )
    recovery_codes = await two_factor.enable_totp(db, user, obj_in.code)
    if recovery_codes is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=INVALID_CODE)

    # The user just proved they hold the new factor: the session counts as a
    # two-factor one from now on.
    set_session_cookie(response, user, mfa=True)
    return RecoveryCodes(recovery_codes=recovery_codes)


@router.post("/totp/disable", status_code=status.HTTP_204_NO_CONTENT)
async def totp_disable(
    obj_in: TotpDisable,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    if not user.totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The authenticator app isn't set up.",
        )
    if not verify_password(obj_in.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )
    if settings.TWO_FACTOR_REQUIRED and not await crud_webauthn_credential.exists_for_user(
        db, user
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is required. Add a passkey before "
            "turning off the authenticator app.",
        )
    await _require_code(db, user, obj_in.code)
    await two_factor.disable_totp(db, user)


@router.post("/recovery-codes", response_model=RecoveryCodes)
async def regenerate_recovery_codes(
    obj_in: TotpCode,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """New recovery codes; the old ones stop working."""
    if not user.totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The authenticator app isn't set up.",
        )
    await _require_code(db, user, obj_in.code)
    return RecoveryCodes(recovery_codes=await two_factor.regenerate_recovery_codes(db, user))
