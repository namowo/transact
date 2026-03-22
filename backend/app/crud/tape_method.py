from app.crud.base import CRUDBase
from app.models.tape_method import TapeMethod
from app.schemas.tape_method import TapeMethodCreate, TapeMethodUpdate


class CRUDTapeMethod(CRUDBase[TapeMethod, TapeMethodCreate, TapeMethodUpdate]):
    def __init__(self):
        super().__init__(TapeMethod)


crud_tape_method = CRUDTapeMethod()
