from typing import Optional

from pydantic import BaseModel, ConfigDict


class GeographicLocationCategoryBase(BaseModel):
    geographic_location_category: Optional[str] = None
    description: Optional[str] = None


class GeographicLocationCategoryCreate(GeographicLocationCategoryBase):
    pass


class GeographicLocationCategoryUpdate(GeographicLocationCategoryBase):
    pass


class GeographicLocationCategoryRead(GeographicLocationCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
