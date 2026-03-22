from app.crud.base import CRUDBase
from app.models.item_category import ItemCategory
from app.schemas.item_category import ItemCategoryCreate, ItemCategoryUpdate


class CRUDItemCategory(CRUDBase[ItemCategory, ItemCategoryCreate, ItemCategoryUpdate]):
    def __init__(self):
        super().__init__(ItemCategory)


crud_item_category = CRUDItemCategory()
