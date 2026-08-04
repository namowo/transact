from app.crud.base import CRUDBase
from app.models.classification_scheme import ClassificationScheme
from app.schemas.classification_scheme import (
    ClassificationSchemeCreate,
    ClassificationSchemeUpdate,
)


class CRUDClassificationScheme(
    CRUDBase[
        ClassificationScheme, ClassificationSchemeCreate, ClassificationSchemeUpdate
    ]
):
    def __init__(self):
        super().__init__(ClassificationScheme)


crud_classification_scheme = CRUDClassificationScheme()
