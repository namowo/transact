from typing import Optional

from pydantic import BaseModel, ConfigDict


class ConditionOfItemPartCategoryBase(BaseModel):
    condition_of_item_part_category: Optional[str] = None
    description: Optional[str] = None


class ConditionOfItemPartCategoryCreate(ConditionOfItemPartCategoryBase):
    pass


class ConditionOfItemPartCategoryUpdate(ConditionOfItemPartCategoryBase):
    pass


class ConditionOfItemPartCategoryRead(ConditionOfItemPartCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
