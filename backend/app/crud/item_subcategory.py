from app.crud.base import CRUDBase
from app.models.item_subcategory import ItemSubcategory
from app.schemas.item_subcategory import ItemSubcategoryCreate, ItemSubcategoryUpdate


class CRUDItemSubcategory(CRUDBase[ItemSubcategory, ItemSubcategoryCreate, ItemSubcategoryUpdate]):
    def __init__(self):
        super().__init__(ItemSubcategory)


crud_item_subcategory = CRUDItemSubcategory()
