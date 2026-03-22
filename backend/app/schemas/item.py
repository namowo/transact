from typing import Optional

from pydantic import BaseModel, ConfigDict


class ItemBase(BaseModel):
    item_category_id: Optional[int] = None
    item_subcategory_id: Optional[int] = None
    description: Optional[str] = None
    picture: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(ItemBase):
    pass


class ItemRead(ItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_category: Optional["ItemCategoryRead"] = None
    item_subcategory: Optional["ItemSubcategoryRead"] = None


from app.schemas.item_category import ItemCategoryRead
from app.schemas.item_subcategory import ItemSubcategoryRead
