from typing import Optional

from pydantic import BaseModel, ConfigDict


class CuttingMethodBase(BaseModel):
    cutting_device_id: Optional[int] = None
    description: Optional[str] = None
    supplier_id: Optional[int] = None


class CuttingMethodCreate(CuttingMethodBase):
    pass


class CuttingMethodUpdate(CuttingMethodBase):
    pass


class CuttingMethodRead(CuttingMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cutting_device: Optional["CuttingDeviceRead"] = None
    supplier: Optional["SupplierRead"] = None


from app.schemas.cutting_device import CuttingDeviceRead
from app.schemas.supplier import SupplierRead
