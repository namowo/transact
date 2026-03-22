from app.crud.base import CRUDBase
from app.models.body_part_condition_category import BodyPartConditionCategory
from app.schemas.body_part_condition_category import BodyPartConditionCategoryCreate, BodyPartConditionCategoryUpdate


class CRUDBodyPartConditionCategory(CRUDBase[BodyPartConditionCategory, BodyPartConditionCategoryCreate, BodyPartConditionCategoryUpdate]):
    def __init__(self):
        super().__init__(BodyPartConditionCategory)


crud_body_part_condition_category = CRUDBodyPartConditionCategory()
