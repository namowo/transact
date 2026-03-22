from typing import Optional

from pydantic import BaseModel, ConfigDict


class EPGAnalysisMethodBase(BaseModel):
    laboratory_id: Optional[int] = None
    genotyping_software: Optional[str] = None
    analytical_threshold: Optional[int] = None
    application_analytical_threshold: Optional[str] = None
    stutter_filter: Optional[str] = None


class EPGAnalysisMethodCreate(EPGAnalysisMethodBase):
    pass


class EPGAnalysisMethodUpdate(EPGAnalysisMethodBase):
    pass


class EPGAnalysisMethodRead(EPGAnalysisMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    laboratory: Optional["LaboratoryRead"] = None


from app.schemas.laboratory import LaboratoryRead
