from typing import Optional

from pydantic import BaseModel, ConfigDict


class ItemSubcategoryBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ItemSubcategoryCreate(ItemSubcategoryBase):
    pass


class ItemSubcategoryUpdate(ItemSubcategoryBase):
    pass


class ItemSubcategoryRead(ItemSubcategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
