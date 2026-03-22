from app.crud.base import CRUDBase
from app.models.vacuum_method import VacuumMethod
from app.schemas.vacuum_method import VacuumMethodCreate, VacuumMethodUpdate


class CRUDVacuumMethod(CRUDBase[VacuumMethod, VacuumMethodCreate, VacuumMethodUpdate]):
    def __init__(self):
        super().__init__(VacuumMethod)


crud_vacuum_method = CRUDVacuumMethod()
