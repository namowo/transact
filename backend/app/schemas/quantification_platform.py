from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class QuantificationPlatformBase(BaseModel):
    name: Optional[str] = None


class QuantificationPlatformCreate(QuantificationPlatformBase):
    pass


class QuantificationPlatformUpdate(QuantificationPlatformBase):
    pass


class QuantificationPlatformRead(QuantificationPlatformBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
