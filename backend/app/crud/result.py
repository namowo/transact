from app.crud.base import CRUDBase
from app.models.result import Result
from app.schemas.result import ResultCreate, ResultUpdate


class CRUDResult(CRUDBase[Result, ResultCreate, ResultUpdate]):
    def __init__(self):
        super().__init__(Result)


crud_result = CRUDResult()
