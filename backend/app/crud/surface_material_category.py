from app.crud.base import CRUDBase
from app.models.surface_material_category import SurfaceMaterialCategory
from app.schemas.surface_material_category import SurfaceMaterialCategoryCreate, SurfaceMaterialCategoryUpdate


class CRUDSurfaceMaterialCategory(CRUDBase[SurfaceMaterialCategory, SurfaceMaterialCategoryCreate, SurfaceMaterialCategoryUpdate]):
    def __init__(self):
        super().__init__(SurfaceMaterialCategory)


crud_surface_material_category = CRUDSurfaceMaterialCategory()
