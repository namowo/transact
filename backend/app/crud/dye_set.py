from app.crud.base import CRUDBase
from app.models.dye_set import DyeSet
from app.schemas.dye_set import DyeSetCreate, DyeSetUpdate


class CRUDDyeSet(CRUDBase[DyeSet, DyeSetCreate, DyeSetUpdate]):
    def __init__(self):
        super().__init__(DyeSet)


crud_dye_set = CRUDDyeSet()
