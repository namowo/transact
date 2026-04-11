from typing import Optional

from pydantic import BaseModel, ConfigDict


class VacuumDeviceBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class VacuumDeviceCreate(VacuumDeviceBase):
    pass


class VacuumDeviceUpdate(VacuumDeviceBase):
    pass


class VacuumDeviceRead(VacuumDeviceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
