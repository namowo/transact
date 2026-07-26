from app.crud.base import CRUDBase
from app.models.quantification_kit import QuantificationKit
from app.schemas.quantification_kit import QuantificationKitCreate, QuantificationKitUpdate


class CRUDQuantificationKit(CRUDBase[QuantificationKit, QuantificationKitCreate, QuantificationKitUpdate]):
    def __init__(self):
        super().__init__(QuantificationKit)


crud_quantification_kit = CRUDQuantificationKit()
