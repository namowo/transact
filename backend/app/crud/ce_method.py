from app.crud.base import CRUDBase
from app.models.ce_method import CEMethod
from app.schemas.ce_method import CEMethodCreate, CEMethodUpdate


class CRUDCEMethod(CRUDBase[CEMethod, CEMethodCreate, CEMethodUpdate]):
    def __init__(self):
        super().__init__(CEMethod)


crud_ce_method = CRUDCEMethod()
