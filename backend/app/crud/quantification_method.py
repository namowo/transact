from app.crud.base import CRUDBase
from app.models.quantification_method import QuantificationMethod
from app.schemas.quantification_method import QuantificationMethodCreate, QuantificationMethodUpdate


class CRUDQuantificationMethod(CRUDBase[QuantificationMethod, QuantificationMethodCreate, QuantificationMethodUpdate]):
    def __init__(self):
        super().__init__(QuantificationMethod)


crud_quantification_method = CRUDQuantificationMethod()
