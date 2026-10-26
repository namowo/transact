from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.item import Item
from app.models.item_category import ItemCategory
from app.models.study import Study
from app.schemas.item import ItemCreate, ItemUpdate

ASSOCIATION_FIELDS = {
    "study_ids": (Study, "studies"),
}


class CRUDItem(CRUDBase[Item, ItemCreate, ItemUpdate]):
    def __init__(self):
        super().__init__(Item)

    async def create(self, db: AsyncSession, obj_in: ItemCreate) -> Item:
        return await self.create_with_associations(
            db, obj_in, association_fields=ASSOCIATION_FIELDS
        )

    async def update(self, db: AsyncSession, id: UUID, obj_in: ItemUpdate) -> Item:
        return await self.update_with_associations(
            db, id, obj_in, association_fields=ASSOCIATION_FIELDS
        )

    async def delete(self, db: AsyncSession, id: UUID) -> None:
        instance = await self.get(db, id)
        if len(instance.studies) > 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete an item that is still linked to other studies.",
            )
        await super().delete(db, id)

    async def get_all_grouped_by_category(self, db: AsyncSession) -> list[Item]:
        """All items, ordered so items sharing an item_category are
        contiguous - lets the caller group them by category in one pass."""
        result = await db.execute(
            select(Item)
            .outerjoin(ItemCategory, Item.item_category_id == ItemCategory.id)
            .order_by(Item.item_category_id.is_(None), ItemCategory.name, Item.id)
        )
        return list(result.scalars().all())


crud_item = CRUDItem()
