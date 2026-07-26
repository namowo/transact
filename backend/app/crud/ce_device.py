from app.crud.base import CRUDBase
from app.models.ce_device import CEDevice
from app.schemas.ce_device import CEDeviceCreate, CEDeviceUpdate


class CRUDCEDevice(CRUDBase[CEDevice, CEDeviceCreate, CEDeviceUpdate]):
    def __init__(self):
        super().__init__(CEDevice)


crud_ce_device = CRUDCEDevice()
