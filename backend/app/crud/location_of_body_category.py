from app.crud.base import CRUDBase
from app.models.location_of_body_category import LocationOfBodyCategory
from app.schemas.location_of_body_category import LocationOfBodyCategoryCreate, LocationOfBodyCategoryUpdate


class CRUDLocationOfBodyCategory(CRUDBase[LocationOfBodyCategory, LocationOfBodyCategoryCreate, LocationOfBodyCategoryUpdate]):
    def __init__(self):
        super().__init__(LocationOfBodyCategory)


crud_location_of_body_category = CRUDLocationOfBodyCategory()
