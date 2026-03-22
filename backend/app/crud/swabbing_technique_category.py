from app.crud.base import CRUDBase
from app.models.swabbing_technique_category import SwabbingTechniqueCategory
from app.schemas.swabbing_technique_category import SwabbingTechniqueCategoryCreate, SwabbingTechniqueCategoryUpdate


class CRUDSwabbingTechniqueCategory(CRUDBase[SwabbingTechniqueCategory, SwabbingTechniqueCategoryCreate, SwabbingTechniqueCategoryUpdate]):
    def __init__(self):
        super().__init__(SwabbingTechniqueCategory)


crud_swabbing_technique_category = CRUDSwabbingTechniqueCategory()
