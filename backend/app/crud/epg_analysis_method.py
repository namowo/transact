from app.crud.base import CRUDBase
from app.models.epg_analysis_method import EPGAnalysisMethod
from app.schemas.epg_analysis_method import EPGAnalysisMethodCreate, EPGAnalysisMethodUpdate


class CRUDEPGAnalysisMethod(CRUDBase[EPGAnalysisMethod, EPGAnalysisMethodCreate, EPGAnalysisMethodUpdate]):
    def __init__(self):
        super().__init__(EPGAnalysisMethod)


crud_epg_analysis_method = CRUDEPGAnalysisMethod()
