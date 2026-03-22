from app.crud.base import CRUDBase
from app.models.condition_of_item_part_category import ConditionOfItemPartCategory
from app.schemas.condition_of_item_part_category import ConditionOfItemPartCategoryCreate, ConditionOfItemPartCategoryUpdate


class CRUDConditionOfItemPartCategory(CRUDBase[ConditionOfItemPartCategory, ConditionOfItemPartCategoryCreate, ConditionOfItemPartCategoryUpdate]):
    def __init__(self):
        super().__init__(ConditionOfItemPartCategory)


crud_condition_of_item_part_category = CRUDConditionOfItemPartCategory()
