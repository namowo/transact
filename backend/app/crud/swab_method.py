from app.crud.base import CRUDBase
from app.models.swab_method import SwabMethod
from app.schemas.swab_method import SwabMethodCreate, SwabMethodUpdate


class CRUDSwabMethod(CRUDBase[SwabMethod, SwabMethodCreate, SwabMethodUpdate]):
    def __init__(self):
        super().__init__(SwabMethod)


crud_swab_method = CRUDSwabMethod()
