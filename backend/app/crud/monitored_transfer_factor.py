from app.crud.base import CRUDBase
from app.models.monitored_transfer_factor import MonitoredTransferFactor
from app.schemas.monitored_transfer_factor import (
    MonitoredTransferFactorCreate,
    MonitoredTransferFactorUpdate,
)


class CRUDMonitoredTransferFactor(
    CRUDBase[
        MonitoredTransferFactor,
        MonitoredTransferFactorCreate,
        MonitoredTransferFactorUpdate,
    ]
):
    def __init__(self):
        super().__init__(MonitoredTransferFactor)


crud_monitored_transfer_factor = CRUDMonitoredTransferFactor()
