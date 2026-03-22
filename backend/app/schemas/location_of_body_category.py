from typing import Optional

from pydantic import BaseModel, ConfigDict


class LocationOfBodyCategoryBase(BaseModel):
    location_of_body_category: Optional[str] = None
    description: Optional[str] = None


class LocationOfBodyCategoryCreate(LocationOfBodyCategoryBase):
    pass


class LocationOfBodyCategoryUpdate(LocationOfBodyCategoryBase):
    pass


class LocationOfBodyCategoryRead(LocationOfBodyCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
