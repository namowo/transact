from app.crud.base import CRUDBase
from app.models.pcr_kit import PCRKit
from app.schemas.pcr_kit import PCRKitCreate, PCRKitUpdate


class CRUDPCRKit(CRUDBase[PCRKit, PCRKitCreate, PCRKitUpdate]):
    def __init__(self):
        super().__init__(PCRKit)


crud_pcr_kit = CRUDPCRKit()
