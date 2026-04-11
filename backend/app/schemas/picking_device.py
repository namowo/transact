from typing import Optional

from pydantic import BaseModel, ConfigDict


class PickingDeviceBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PickingDeviceCreate(PickingDeviceBase):
    pass


class PickingDeviceUpdate(PickingDeviceBase):
    pass


class PickingDeviceRead(PickingDeviceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
