from app.crud.base import CRUDBase
from app.models.classification_criteria import ClassificationCriteria
from app.schemas.classification_criteria import (
    ClassificationCriteriaCreate,
    ClassificationCriteriaUpdate,
)


class CRUDClassificationCriteria(
    CRUDBase[
        ClassificationCriteria, ClassificationCriteriaCreate, ClassificationCriteriaUpdate
    ]
):
    def __init__(self):
        super().__init__(ClassificationCriteria)


crud_classification_criteria = CRUDClassificationCriteria()
