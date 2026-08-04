from typing import Optional

from pydantic import BaseModel, ConfigDict


class ItemPartsCategoryBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    item_category_id: Optional[int] = None


class ItemPartsCategoryCreate(ItemPartsCategoryBase):
    pass


class ItemPartsCategoryUpdate(ItemPartsCategoryBase):
    pass


class ItemPartsCategoryRead(ItemPartsCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_category: Optional["ItemCategoryRead"] = None


from app.schemas.item_category import ItemCategoryRead
