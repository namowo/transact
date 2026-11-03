from app.crud.base import CRUDBase
from app.models.item_surface_material_category import ItemSurfaceMaterialCategory
from app.schemas.item_surface_material_category import (
    ItemSurfaceMaterialCategoryCreate,
    ItemSurfaceMaterialCategoryUpdate,
)


class CRUDItemSurfaceMaterialCategory(
    CRUDBase[
        ItemSurfaceMaterialCategory,
        ItemSurfaceMaterialCategoryCreate,
        ItemSurfaceMaterialCategoryUpdate,
    ]
):
    def __init__(self):
        super().__init__(ItemSurfaceMaterialCategory)


crud_item_surface_material_category = CRUDItemSurfaceMaterialCategory()
