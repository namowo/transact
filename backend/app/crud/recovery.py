from app.crud.base import CRUDBase
from app.models.recovery import Recovery
from app.schemas.recovery import RecoveryCreate, RecoveryUpdate


class CRUDRecovery(CRUDBase[Recovery, RecoveryCreate, RecoveryUpdate]):
    def __init__(self):
        super().__init__(Recovery)


crud_recovery = CRUDRecovery()
