from app.crud.base import CRUDBase
from app.models.type_of_swab_category import TypeOfSwabCategory
from app.schemas.type_of_swab_category import TypeOfSwabCategoryCreate, TypeOfSwabCategoryUpdate


class CRUDTypeOfSwabCategory(CRUDBase[TypeOfSwabCategory, TypeOfSwabCategoryCreate, TypeOfSwabCategoryUpdate]):
    def __init__(self):
        super().__init__(TypeOfSwabCategory)


crud_type_of_swab_category = CRUDTypeOfSwabCategory()
