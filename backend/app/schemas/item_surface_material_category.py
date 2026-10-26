from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ItemSurfaceMaterialCategoryBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ItemSurfaceMaterialCategoryCreate(ItemSurfaceMaterialCategoryBase):
    pass


class ItemSurfaceMaterialCategoryUpdate(ItemSurfaceMaterialCategoryBase):
    pass


class ItemSurfaceMaterialCategoryRead(ItemSurfaceMaterialCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
