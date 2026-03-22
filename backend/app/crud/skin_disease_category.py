from app.crud.base import CRUDBase
from app.models.skin_disease_category import SkinDiseaseCategory
from app.schemas.skin_disease_category import SkinDiseaseCategoryCreate, SkinDiseaseCategoryUpdate


class CRUDSkinDiseaseCategory(CRUDBase[SkinDiseaseCategory, SkinDiseaseCategoryCreate, SkinDiseaseCategoryUpdate]):
    def __init__(self):
        super().__init__(SkinDiseaseCategory)


crud_skin_disease_category = CRUDSkinDiseaseCategory()
