from typing import Optional

from pydantic import BaseModel, ConfigDict


class ItemSubcategoryBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    item_category_id: Optional[int] = None


class ItemSubcategoryCreate(ItemSubcategoryBase):
    pass


class ItemSubcategoryUpdate(ItemSubcategoryBase):
    pass


class ItemSubcategoryRead(ItemSubcategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_category: Optional["ItemCategoryRead"] = None


from app.schemas.item_category import ItemCategoryRead
