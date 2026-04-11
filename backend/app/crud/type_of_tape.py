from app.crud.base import CRUDBase
from app.models.type_of_tape import TypeOfTape
from app.schemas.type_of_tape import TypeOfTapeCreate, TypeOfTapeUpdate


class CRUDTypeOfTape(CRUDBase[TypeOfTape, TypeOfTapeCreate, TypeOfTapeUpdate]):
    def __init__(self):
        super().__init__(TypeOfTape)


crud_type_of_tape = CRUDTypeOfTape()
