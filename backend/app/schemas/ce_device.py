from typing import Optional

from pydantic import BaseModel, ConfigDict


class CEDeviceBase(BaseModel):
    name: Optional[str] = None


class CEDeviceCreate(CEDeviceBase):
    pass


class CEDeviceUpdate(CEDeviceBase):
    pass


class CEDeviceRead(CEDeviceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
