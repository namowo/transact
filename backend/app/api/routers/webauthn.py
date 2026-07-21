import json
from datetime import timedelta
from typing import List

import webauthn
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.exceptions import WebAuthnException
from webauthn.helpers.structs import PublicKeyCredentialDescriptor

from app.api.routers.auth import set_session_cookie
from app.core.config import settings
from app.core.deps import current_active_user, get_async_session
from app.crud.user import crud_user
from app.crud.webauthn_challenge import crud_webauthn_challenge
from app.crud.webauthn_credential import crud_webauthn_credential
from app.models.user import User
from app.schemas.user import UserRead
from app.schemas.webauthn import (
    WebAuthnCredentialRead,
    WebAuthnLoginOptionsRequest,
    WebAuthnLoginVerify,
    WebAuthnRegisterVerify,
)

router = APIRouter()

REGISTER_PURPOSE = "register"
LOGIN_PURPOSE = "login"

CHALLENGE_TTL = timedelta(seconds=settings.WEBAUTHN_CHALLENGE_TTL_SECONDS)


@router.post("/register/options")
async def register_options(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    existing = await crud_webauthn_credential.list_for_user(db, user)
    options = webauthn.generate_registration_options(
        rp_id=settings.WEBAUTHN_RP_ID,
        rp_name=settings.WEBAUTHN_RP_NAME,
        user_id=str(user.id).encode("utf-8"),
        user_name=user.email,
        user_display_name=f"{user.first_name} {user.last_name}",
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(credential.credential_id))
            for credential in existing
        ],
    )

    await crud_webauthn_challenge.store(
        db,
        user,
        REGISTER_PURPOSE,
        bytes_to_base64url(options.challenge),
        CHALLENGE_TTL,
    )

    return json.loads(webauthn.options_to_json(options))


@router.post("/register/verify", response_model=WebAuthnCredentialRead)
async def register_verify(
    obj_in: WebAuthnRegisterVerify,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    challenge = await crud_webauthn_challenge.get_valid(db, user, REGISTER_PURPOSE)
    if challenge is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This registration request has expired. Please try again.",
        )

    try:
        verification = webauthn.verify_registration_response(
            credential=obj_in.credential,
            expected_challenge=base64url_to_bytes(challenge),
            expected_rp_id=settings.WEBAUTHN_RP_ID,
            expected_origin=settings.WEBAUTHN_ORIGIN,
        )
    except WebAuthnException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not verify this passkey. Please try again.",
        )

    credential = await crud_webauthn_credential.create(
        db,
        user,
        credential_id=bytes_to_base64url(verification.credential_id),
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count,
        device_name=obj_in.device_name,
    )
    return credential


@router.post("/login/options")
async def login_options(
    obj_in: WebAuthnLoginOptionsRequest,
    db: AsyncSession = Depends(get_async_session),
):
    user = await crud_user.get_by_email(db, obj_in.email)
    credentials = await crud_webauthn_credential.list_for_user(db, user) if user else []
    if user is None or not credentials:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No passkey is registered for this account.",
        )

    options = webauthn.generate_authentication_options(
        rp_id=settings.WEBAUTHN_RP_ID,
        allow_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(credential.credential_id))
            for credential in credentials
        ],
    )

    await crud_webauthn_challenge.store(
        db,
        user,
        LOGIN_PURPOSE,
        bytes_to_base64url(options.challenge),
        CHALLENGE_TTL,
    )

    return json.loads(webauthn.options_to_json(options))


@router.post("/login/verify", response_model=UserRead)
async def login_verify(
    obj_in: WebAuthnLoginVerify,
    response: Response,
    db: AsyncSession = Depends(get_async_session),
):
    user = await crud_user.get_by_email(db, obj_in.email)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not verify this passkey.",
        )

    challenge = await crud_webauthn_challenge.get_valid(db, user, LOGIN_PURPOSE)
    if challenge is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This login request has expired. Please try again.",
        )

    credential_id = obj_in.credential.get("id")
    credential = (
        await crud_webauthn_credential.get_by_credential_id(db, credential_id)
        if credential_id
        else None
    )
    if credential is None or credential.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not verify this passkey.",
        )

    try:
        verification = webauthn.verify_authentication_response(
            credential=obj_in.credential,
            expected_challenge=base64url_to_bytes(challenge),
            expected_rp_id=settings.WEBAUTHN_RP_ID,
            expected_origin=settings.WEBAUTHN_ORIGIN,
            credential_public_key=credential.public_key,
            credential_current_sign_count=credential.sign_count,
        )
    except WebAuthnException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not verify this passkey.",
        )

    await crud_webauthn_credential.update_sign_count(
        db, credential, verification.new_sign_count
    )

    set_session_cookie(response, user)
    return user


@router.get("/credentials", response_model=List[WebAuthnCredentialRead])
async def list_credentials(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    return await crud_webauthn_credential.list_for_user(db, user)


@router.delete("/credentials/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(
    credential_id: int,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    deleted = await crud_webauthn_credential.delete_for_user(db, user, credential_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Passkey not found."
        )
