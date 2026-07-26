from typing import Optional

from pydantic import BaseModel, ConfigDict


class VacuumMethodBase(BaseModel):
    vacuum_device_id: Optional[int] = None
    description: Optional[str] = None
    supplier_id: Optional[int] = None


class VacuumMethodCreate(VacuumMethodBase):
    pass


class VacuumMethodUpdate(VacuumMethodBase):
    pass


class VacuumMethodRead(VacuumMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vacuum_device: Optional["VacuumDeviceRead"] = None
    supplier: Optional["SupplierRead"] = None


from app.schemas.vacuum_device import VacuumDeviceRead
from app.schemas.supplier import SupplierRead
