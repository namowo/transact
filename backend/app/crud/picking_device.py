from app.crud.base import CRUDBase
from app.models.picking_device import PickingDevice
from app.schemas.picking_device import PickingDeviceCreate, PickingDeviceUpdate


class CRUDPickingDevice(CRUDBase[PickingDevice, PickingDeviceCreate, PickingDeviceUpdate]):
    def __init__(self):
        super().__init__(PickingDevice)


crud_picking_device = CRUDPickingDevice()
