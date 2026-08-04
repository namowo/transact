from app.crud.base import CRUDBase
from app.models.inhibition_category import InhibitionCategory
from app.schemas.inhibition_category import (
    InhibitionCategoryCreate,
    InhibitionCategoryUpdate,
)


class CRUDInhibitionCategory(
    CRUDBase[InhibitionCategory, InhibitionCategoryCreate, InhibitionCategoryUpdate]
):
    def __init__(self):
        super().__init__(InhibitionCategory)


crud_inhibition_category = CRUDInhibitionCategory()
