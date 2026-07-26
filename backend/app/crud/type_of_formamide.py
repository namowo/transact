from app.crud.base import CRUDBase
from app.models.type_of_formamide import TypeOfFormamide
from app.schemas.type_of_formamide import TypeOfFormamideCreate, TypeOfFormamideUpdate


class CRUDTypeOfFormamide(CRUDBase[TypeOfFormamide, TypeOfFormamideCreate, TypeOfFormamideUpdate]):
    def __init__(self):
        super().__init__(TypeOfFormamide)


crud_type_of_formamide = CRUDTypeOfFormamide()
