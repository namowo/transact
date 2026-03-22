from typing import Optional

from pydantic import BaseModel, ConfigDict


class ItemCategoryBase(BaseModel):
    item_category: Optional[str] = None
    description: Optional[str] = None


class ItemCategoryCreate(ItemCategoryBase):
    pass


class ItemCategoryUpdate(ItemCategoryBase):
    pass


class ItemCategoryRead(ItemCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
