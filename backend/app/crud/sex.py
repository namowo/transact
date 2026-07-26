from app.crud.base import CRUDBase
from app.models.sex import Sex
from app.schemas.sex import SexCreate, SexUpdate


class CRUDSex(CRUDBase[Sex, SexCreate, SexUpdate]):
    def __init__(self):
        super().__init__(Sex)


crud_sex = CRUDSex()
