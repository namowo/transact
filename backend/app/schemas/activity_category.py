from typing import Optional

from pydantic import BaseModel, ConfigDict


class ActivityCategoryBase(BaseModel):
    activity_category: Optional[str] = None
    description: Optional[str] = None


class ActivityCategoryCreate(ActivityCategoryBase):
    pass


class ActivityCategoryUpdate(ActivityCategoryBase):
    pass


class ActivityCategoryRead(ActivityCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
