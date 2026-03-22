from app.crud.base import CRUDBase
from app.models.epg_interpretation_method import EPGInterpretationMethod
from app.schemas.epg_interpretation_method import EPGInterpretationMethodCreate, EPGInterpretationMethodUpdate


class CRUDEPGInterpretationMethod(CRUDBase[EPGInterpretationMethod, EPGInterpretationMethodCreate, EPGInterpretationMethodUpdate]):
    def __init__(self):
        super().__init__(EPGInterpretationMethod)


crud_epg_interpretation_method = CRUDEPGInterpretationMethod()
