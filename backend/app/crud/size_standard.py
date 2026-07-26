from app.crud.base import CRUDBase
from app.models.size_standard import SizeStandard
from app.schemas.size_standard import SizeStandardCreate, SizeStandardUpdate


class CRUDSizeStandard(CRUDBase[SizeStandard, SizeStandardCreate, SizeStandardUpdate]):
    def __init__(self):
        super().__init__(SizeStandard)


crud_size_standard = CRUDSizeStandard()
