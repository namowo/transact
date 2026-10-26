from app.crud.base import CRUDBase
from app.models.quantification_platform import QuantificationPlatform
from app.schemas.quantification_platform import QuantificationPlatformCreate, QuantificationPlatformUpdate


class CRUDQuantificationPlatform(CRUDBase[QuantificationPlatform, QuantificationPlatformCreate, QuantificationPlatformUpdate]):
    def __init__(self):
        super().__init__(QuantificationPlatform)


crud_quantification_platform = CRUDQuantificationPlatform()
