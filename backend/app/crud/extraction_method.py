from app.crud.base import CRUDBase
from app.models.extraction_method import ExtractionMethod
from app.schemas.extraction_method import ExtractionMethodCreate, ExtractionMethodUpdate


class CRUDExtractionMethod(CRUDBase[ExtractionMethod, ExtractionMethodCreate, ExtractionMethodUpdate]):
    def __init__(self):
        super().__init__(ExtractionMethod)


crud_extraction_method = CRUDExtractionMethod()
