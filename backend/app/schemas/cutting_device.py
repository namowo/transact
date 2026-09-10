from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class CuttingDeviceBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CuttingDeviceCreate(CuttingDeviceBase):
    pass


class CuttingDeviceUpdate(CuttingDeviceBase):
    pass


class CuttingDeviceRead(CuttingDeviceBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
