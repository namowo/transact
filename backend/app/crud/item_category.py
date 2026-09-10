from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.item_category import ItemCategory
from app.schemas.item_category import ItemCategoryCreate, ItemCategoryUpdate


class CRUDItemCategory(CRUDBase[ItemCategory, ItemCategoryCreate, ItemCategoryUpdate]):
    def __init__(self):
        super().__init__(ItemCategory)

    async def create(
        self, db: AsyncSession, obj_in: ItemCategoryCreate
    ) -> ItemCategory:
        # Guards against duplicate categories from double-submitted requests
        # (e.g. a double click) - reuse the existing row instead of
        # inserting a second one with the same name.
        if obj_in.name:
            result = await db.execute(
                select(ItemCategory).where(
                    func.lower(ItemCategory.name) == obj_in.name.strip().lower()
                )
            )
            existing = result.scalars().first()
            if existing is not None:
                return existing

        return await super().create(db, obj_in)


crud_item_category = CRUDItemCategory()
