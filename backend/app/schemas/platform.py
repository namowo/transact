from typing import Optional

from pydantic import BaseModel, ConfigDict


class PlatformBase(BaseModel):
    name: Optional[str] = None


class PlatformCreate(PlatformBase):
    pass


class PlatformUpdate(PlatformBase):
    pass


class PlatformRead(PlatformBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
