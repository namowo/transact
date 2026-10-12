from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.item_parts_category import ItemPartsCategory
from app.schemas.item_parts_category import ItemPartsCategoryCreate, ItemPartsCategoryUpdate


class CRUDItemPartsCategory(CRUDBase[ItemPartsCategory, ItemPartsCategoryCreate, ItemPartsCategoryUpdate]):
    def __init__(self):
        super().__init__(ItemPartsCategory)

    async def create(
        self, db: AsyncSession, obj_in: ItemPartsCategoryCreate
    ) -> ItemPartsCategory:
        # Guards against duplicate item parts from double-submitted requests
        # (e.g. a double click) - reuse the existing row for the same name
        # within the same item category instead of inserting a second one.
        if obj_in.name:
            result = await db.execute(
                select(ItemPartsCategory).where(
                    func.lower(ItemPartsCategory.name) == obj_in.name.strip().lower(),
                    ItemPartsCategory.item_category_id == obj_in.item_category_id,
                )
            )
            existing = result.scalars().first()
            if existing is not None:
                return existing

        return await super().create(db, obj_in)


crud_item_parts_category = CRUDItemPartsCategory()
