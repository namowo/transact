from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.item import Item
from app.models.item_category import ItemCategory
from app.schemas.item import ItemCreate, ItemUpdate


class CRUDItem(CRUDBase[Item, ItemCreate, ItemUpdate]):
    def __init__(self):
        super().__init__(Item)

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
