from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class LocationOfBodyCategoryBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class LocationOfBodyCategoryCreate(LocationOfBodyCategoryBase):
    pass


class LocationOfBodyCategoryUpdate(LocationOfBodyCategoryBase):
    pass


class LocationOfBodyCategoryRead(LocationOfBodyCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
