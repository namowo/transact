from app.crud.base import CRUDBase
from app.models.disturbance_category import DisturbanceCategory
from app.schemas.disturbance_category import DisturbanceCategoryCreate, DisturbanceCategoryUpdate


class CRUDDisturbanceCategory(CRUDBase[DisturbanceCategory, DisturbanceCategoryCreate, DisturbanceCategoryUpdate]):
    def __init__(self):
        super().__init__(DisturbanceCategory)


crud_disturbance_category = CRUDDisturbanceCategory()
