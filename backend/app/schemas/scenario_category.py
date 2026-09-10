from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ScenarioCategoryBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ScenarioCategoryCreate(ScenarioCategoryBase):
    pass


class ScenarioCategoryUpdate(ScenarioCategoryBase):
    pass


class ScenarioCategoryRead(ScenarioCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
