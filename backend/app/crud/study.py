from app.crud.base import CRUDBase
from app.models.study import Study
from app.schemas.study import StudyCreate, StudyUpdate


class CRUDStudy(CRUDBase[Study, StudyCreate, StudyUpdate]):
    def __init__(self):
        super().__init__(Study)


crud_study = CRUDStudy()
