from typing import Optional

from pydantic import BaseModel, ConfigDict


class ItemPartsCategoryBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ItemPartsCategoryCreate(ItemPartsCategoryBase):
    pass


class ItemPartsCategoryUpdate(ItemPartsCategoryBase):
    pass


class ItemPartsCategoryRead(ItemPartsCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
