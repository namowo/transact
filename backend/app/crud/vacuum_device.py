from app.crud.base import CRUDBase
from app.models.vacuum_device import VacuumDevice
from app.schemas.vacuum_device import VacuumDeviceCreate, VacuumDeviceUpdate


class CRUDVacuumDevice(CRUDBase[VacuumDevice, VacuumDeviceCreate, VacuumDeviceUpdate]):
    def __init__(self):
        super().__init__(VacuumDevice)


crud_vacuum_device = CRUDVacuumDevice()
