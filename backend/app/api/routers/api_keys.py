from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_active_user, get_async_session
from app.crud.api_key import crud_api_key
from app.models.user import User
from app.schemas.api_key import ApiKeyCreate, ApiKeyCreated, ApiKeyRead

router = APIRouter()


@router.get("", response_model=List[ApiKeyRead])
async def list_api_keys(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    return await crud_api_key.list_for_user(db, user)


@router.post("", response_model=ApiKeyCreated, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    obj_in: ApiKeyCreate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    api_key, token = await crud_api_key.create(
        db, user, name=obj_in.name, expires_at=obj_in.expires_at
    )
    return ApiKeyCreated(token=token, **ApiKeyRead.model_validate(api_key).model_dump())


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    api_key_id: UUID,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    revoked = await crud_api_key.revoke_for_user(db, user, api_key_id)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found."
        )
