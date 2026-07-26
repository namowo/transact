from app.crud.base import CRUDBase
from app.models.recovery_set import RecoverySet
from app.schemas.recovery_set import RecoverySetCreate, RecoverySetUpdate


class CRUDRecoverySet(CRUDBase[RecoverySet, RecoverySetCreate, RecoverySetUpdate]):
    def __init__(self):
        super().__init__(RecoverySet)


crud_recovery_set = CRUDRecoverySet()
