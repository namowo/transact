from typing import Optional

from pydantic import BaseModel, ConfigDict


class PickingMethodBase(BaseModel):
    picking_device_id: Optional[int] = None
    description: Optional[str] = None
    supplier_id: Optional[int] = None


class PickingMethodCreate(PickingMethodBase):
    pass


class PickingMethodUpdate(PickingMethodBase):
    pass


class PickingMethodRead(PickingMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    picking_device: Optional["PickingDeviceRead"] = None
    supplier: Optional["SupplierRead"] = None


from app.schemas.picking_device import PickingDeviceRead
from app.schemas.supplier import SupplierRead
