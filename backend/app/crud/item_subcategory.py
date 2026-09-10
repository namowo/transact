from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.item_subcategory import ItemSubcategory
from app.schemas.item_subcategory import ItemSubcategoryCreate, ItemSubcategoryUpdate


class CRUDItemSubcategory(CRUDBase[ItemSubcategory, ItemSubcategoryCreate, ItemSubcategoryUpdate]):
    def __init__(self):
        super().__init__(ItemSubcategory)

    async def create(
        self, db: AsyncSession, obj_in: ItemSubcategoryCreate
    ) -> ItemSubcategory:
        # Guards against duplicate subcategories from double-submitted
        # requests (e.g. a double click) - reuse the existing row for the
        # same name within the same category instead of inserting a second
        # one.
        if obj_in.name:
            result = await db.execute(
                select(ItemSubcategory).where(
                    func.lower(ItemSubcategory.name) == obj_in.name.strip().lower(),
                    ItemSubcategory.item_category_id == obj_in.item_category_id,
                )
            )
            existing = result.scalars().first()
            if existing is not None:
                return existing

        return await super().create(db, obj_in)


crud_item_subcategory = CRUDItemSubcategory()
