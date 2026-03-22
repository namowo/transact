from app.crud.base import CRUDBase
from app.models.laboratory import Laboratory
from app.schemas.laboratory import LaboratoryCreate, LaboratoryUpdate


class CRUDLaboratory(CRUDBase[Laboratory, LaboratoryCreate, LaboratoryUpdate]):
    def __init__(self):
        super().__init__(Laboratory)


crud_laboratory = CRUDLaboratory()
