from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class EPGAnalysisMethodBase(BaseModel):
    laboratory_id: Optional[UUID] = None
    genotyping_software_id: Optional[UUID] = None
    analytical_threshold: Optional[int] = None
    application_analytical_threshold: Optional[str] = None
    stutter_filter: Optional[str] = None


class EPGAnalysisMethodCreate(EPGAnalysisMethodBase):
    pass


class EPGAnalysisMethodUpdate(EPGAnalysisMethodBase):
    pass


class EPGAnalysisMethodRead(EPGAnalysisMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    laboratory: Optional["LaboratoryRead"] = None
    genotyping_software: Optional["GenotypingSoftwareRead"] = None


from app.schemas.laboratory import LaboratoryRead
from app.schemas.genotyping_software import GenotypingSoftwareRead
