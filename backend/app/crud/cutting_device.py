from app.crud.base import CRUDBase
from app.models.cutting_device import CuttingDevice
from app.schemas.cutting_device import CuttingDeviceCreate, CuttingDeviceUpdate


class CRUDCuttingDevice(CRUDBase[CuttingDevice, CuttingDeviceCreate, CuttingDeviceUpdate]):
    def __init__(self):
        super().__init__(CuttingDevice)


crud_cutting_device = CRUDCuttingDevice()
