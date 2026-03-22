from typing import Optional

from pydantic import BaseModel, ConfigDict


class ScenarioCategoryBase(BaseModel):
    scenario_category: Optional[str] = None
    description: Optional[str] = None


class ScenarioCategoryCreate(ScenarioCategoryBase):
    pass


class ScenarioCategoryUpdate(ScenarioCategoryBase):
    pass


class ScenarioCategoryRead(ScenarioCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
