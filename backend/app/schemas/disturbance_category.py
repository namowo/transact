from typing import Optional

from pydantic import BaseModel, ConfigDict


class DisturbanceCategoryBase(BaseModel):
    disturbance_category: Optional[str] = None
    description: Optional[str] = None


class DisturbanceCategoryCreate(DisturbanceCategoryBase):
    pass


class DisturbanceCategoryUpdate(DisturbanceCategoryBase):
    pass


class DisturbanceCategoryRead(DisturbanceCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
