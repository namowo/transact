from typing import Optional

from pydantic import BaseModel, ConfigDict


class SurfaceMaterialCategoryBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class SurfaceMaterialCategoryCreate(SurfaceMaterialCategoryBase):
    pass


class SurfaceMaterialCategoryUpdate(SurfaceMaterialCategoryBase):
    pass


class SurfaceMaterialCategoryRead(SurfaceMaterialCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
