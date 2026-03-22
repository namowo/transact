from app.crud.base import CRUDBase
from app.models.cutting_method import CuttingMethod
from app.schemas.cutting_method import CuttingMethodCreate, CuttingMethodUpdate


class CRUDCuttingMethod(CRUDBase[CuttingMethod, CuttingMethodCreate, CuttingMethodUpdate]):
    def __init__(self):
        super().__init__(CuttingMethod)


crud_cutting_method = CRUDCuttingMethod()
