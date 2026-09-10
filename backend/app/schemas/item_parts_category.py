from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ItemPartsCategoryBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    item_category_id: Optional[UUID] = None


class ItemPartsCategoryCreate(ItemPartsCategoryBase):
    pass


class ItemPartsCategoryUpdate(ItemPartsCategoryBase):
    pass


class ItemPartsCategoryRead(ItemPartsCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item_category: Optional["ItemCategoryRead"] = None


from app.schemas.item_category import ItemCategoryRead
