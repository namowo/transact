from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class DyeChannelBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class DyeChannelCreate(DyeChannelBase):
    pass


class DyeChannelUpdate(DyeChannelBase):
    pass


class DyeChannelRead(DyeChannelBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
