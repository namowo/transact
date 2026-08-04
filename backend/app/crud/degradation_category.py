from app.crud.base import CRUDBase
from app.models.degradation_category import DegradationCategory
from app.schemas.degradation_category import (
    DegradationCategoryCreate,
    DegradationCategoryUpdate,
)


class CRUDDegradationCategory(
    CRUDBase[DegradationCategory, DegradationCategoryCreate, DegradationCategoryUpdate]
):
    def __init__(self):
        super().__init__(DegradationCategory)


crud_degradation_category = CRUDDegradationCategory()
