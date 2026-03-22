from app.crud.base import CRUDBase
from app.models.principle_of_quant_method_category import PrincipleOfQuantMethodCategory
from app.schemas.principle_of_quant_method_category import PrincipleOfQuantMethodCategoryCreate, PrincipleOfQuantMethodCategoryUpdate


class CRUDPrincipleOfQuantMethodCategory(CRUDBase[PrincipleOfQuantMethodCategory, PrincipleOfQuantMethodCategoryCreate, PrincipleOfQuantMethodCategoryUpdate]):
    def __init__(self):
        super().__init__(PrincipleOfQuantMethodCategory)


crud_principle_of_quant_method_category = CRUDPrincipleOfQuantMethodCategory()
