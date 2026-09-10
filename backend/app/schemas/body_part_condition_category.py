from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class BodyPartConditionCategoryBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class BodyPartConditionCategoryCreate(BodyPartConditionCategoryBase):
    pass


class BodyPartConditionCategoryUpdate(BodyPartConditionCategoryBase):
    pass


class BodyPartConditionCategoryRead(BodyPartConditionCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
