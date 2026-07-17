from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_active_user, get_async_session
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate

router = APIRouter()

_crud_user_update = CRUDBase(User)


@router.get("/me", response_model=UserRead)
async def read_me(user: User = Depends(current_active_user)):
    return user


@router.patch("/me", response_model=UserRead)
async def update_me(
    obj_in: UserUpdate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    return await _crud_user_update.update(db, user.id, obj_in)
