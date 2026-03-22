from app.crud.base import CRUDBase
from app.models.pcr_method import PCRMethod
from app.schemas.pcr_method import PCRMethodCreate, PCRMethodUpdate


class CRUDPCRMethod(CRUDBase[PCRMethod, PCRMethodCreate, PCRMethodUpdate]):
    def __init__(self):
        super().__init__(PCRMethod)


crud_pcr_method = CRUDPCRMethod()
