from typing import Optional

from pydantic import BaseModel, ConfigDict


class ExperienceLevelBase(BaseModel):
    name: Optional[str] = None


class ExperienceLevelCreate(ExperienceLevelBase):
    pass


class ExperienceLevelUpdate(ExperienceLevelBase):
    pass


class ExperienceLevelRead(ExperienceLevelBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
