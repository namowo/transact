from typing import Optional

from pydantic import BaseModel, ConfigDict


class DegradationCategoryBase(BaseModel):
    name: Optional[str] = None


class DegradationCategoryCreate(DegradationCategoryBase):
    pass


class DegradationCategoryUpdate(DegradationCategoryBase):
    pass


class DegradationCategoryRead(DegradationCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
