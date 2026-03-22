from app.crud.base import CRUDBase
from app.models.item_parts_category import ItemPartsCategory
from app.schemas.item_parts_category import ItemPartsCategoryCreate, ItemPartsCategoryUpdate


class CRUDItemPartsCategory(CRUDBase[ItemPartsCategory, ItemPartsCategoryCreate, ItemPartsCategoryUpdate]):
    def __init__(self):
        super().__init__(ItemPartsCategory)


crud_item_parts_category = CRUDItemPartsCategory()
