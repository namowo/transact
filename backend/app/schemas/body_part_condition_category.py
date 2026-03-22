from typing import Optional

from pydantic import BaseModel, ConfigDict


class BodyPartConditionCategoryBase(BaseModel):
    body_part_condition_category: Optional[str] = None
    description: Optional[str] = None


class BodyPartConditionCategoryCreate(BodyPartConditionCategoryBase):
    pass


class BodyPartConditionCategoryUpdate(BodyPartConditionCategoryBase):
    pass


class BodyPartConditionCategoryRead(BodyPartConditionCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
