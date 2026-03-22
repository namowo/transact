from app.crud.base import CRUDBase
from app.models.activity_category import ActivityCategory
from app.schemas.activity_category import ActivityCategoryCreate, ActivityCategoryUpdate


class CRUDActivityCategory(CRUDBase[ActivityCategory, ActivityCategoryCreate, ActivityCategoryUpdate]):
    def __init__(self):
        super().__init__(ActivityCategory)


crud_activity_category = CRUDActivityCategory()
