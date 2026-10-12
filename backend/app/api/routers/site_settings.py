from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_superuser, get_async_session
from app.crud.site_settings import crud_site_settings as crud
from app.schemas.site_settings import (
    SiteSettingsRead as ReadSchema,
    SiteSettingsUpdate as UpdateSchema,
)

router = APIRouter()


@router.get("", response_model=ReadSchema)
async def get_site_settings(db: AsyncSession = Depends(get_async_session)):
    return await crud.get(db)


@router.patch(
    "",
    response_model=ReadSchema,
    dependencies=[Depends(current_superuser)],
)
async def update_site_settings(
    obj_in: UpdateSchema, db: AsyncSession = Depends(get_async_session)
):
    return await crud.update(db, obj_in)
