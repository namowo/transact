from app.crud.base import CRUDBase
from app.models.geographic_location_category import GeographicLocationCategory
from app.schemas.geographic_location_category import GeographicLocationCategoryCreate, GeographicLocationCategoryUpdate


class CRUDGeographicLocationCategory(CRUDBase[GeographicLocationCategory, GeographicLocationCategoryCreate, GeographicLocationCategoryUpdate]):
    def __init__(self):
        super().__init__(GeographicLocationCategory)


crud_geographic_location_category = CRUDGeographicLocationCategory()
