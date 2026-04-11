from typing import Optional

from pydantic import BaseModel, ConfigDict


class CuttingMethodBase(BaseModel):
    cutting_device_id: Optional[int] = None
    description: Optional[str] = None
    catalogue_number_of_supplier: Optional[str] = None
    full_name_as_by_supplier: Optional[str] = None
    supplier: Optional[str] = None


class CuttingMethodCreate(CuttingMethodBase):
    pass


class CuttingMethodUpdate(CuttingMethodBase):
    pass


class CuttingMethodRead(CuttingMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cutting_device: Optional["CuttingDeviceRead"] = None


from app.schemas.cutting_device import CuttingDeviceRead
