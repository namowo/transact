from typing import Optional
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_model import DataModel
from app.models.user import User
from app.schemas.data_model import DataModelCreate, DataModelUpdate


class CRUDDataModel:
    async def get(self, db: AsyncSession, id: UUID) -> Optional[DataModel]:
        return await db.get(DataModel, id)

    async def list_visible(self, db: AsyncSession, user: Optional[User]) -> list[DataModel]:
        """Public models plus, for signed-in users, their own."""
        condition = DataModel.is_public.is_(True)
        if user is not None:
            condition = or_(condition, DataModel.owner_id == user.id)
        result = await db.execute(
            select(DataModel).where(condition).order_by(func.lower(DataModel.name))
        )
        return list(result.scalars())

    async def create(self, db: AsyncSession, obj_in: DataModelCreate, owner: User) -> DataModel:
        instance = DataModel(
            owner_id=owner.id,
            name=obj_in.name,
            description=obj_in.description,
            definition=obj_in.definition.model_dump(mode="json"),
            is_public=obj_in.is_public,
        )
        db.add(instance)
        await db.commit()
        await db.refresh(instance)
        return instance

    async def update(
        self, db: AsyncSession, instance: DataModel, obj_in: DataModelUpdate
    ) -> DataModel:
        data = obj_in.model_dump(exclude_unset=True, mode="json")
        for field in ("name", "description", "is_public", "definition"):
            if field in data and (data[field] is not None or field == "description"):
                setattr(instance, field, data[field])
        instance.updated_at = func.now()
        await db.commit()
        await db.refresh(instance)
        return instance

    async def delete(self, db: AsyncSession, instance: DataModel) -> None:
        await db.delete(instance)
        await db.commit()


crud_data_model = CRUDDataModel()
