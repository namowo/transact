from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class EPGInterpretationMethodBase(BaseModel):
    laboratory_id: Optional[UUID] = None
    determination_of_noc: Optional[str] = None
    statistical_software_id: Optional[UUID] = None
    parameters_modelled_by_software: Optional[str] = None
    allele_frequency_database: Optional[str] = None
    application_analytical_threshold_id: Optional[UUID] = None
    stutter_filter_id: Optional[UUID] = None


class EPGInterpretationMethodCreate(EPGInterpretationMethodBase):
    pass


class EPGInterpretationMethodUpdate(EPGInterpretationMethodBase):
    pass


class EPGInterpretationMethodRead(EPGInterpretationMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    laboratory: Optional["LaboratoryRead"] = None
    statistical_software: Optional["StatisticalSoftwareRead"] = None
    application_analytical_threshold: Optional[
        "ApplicationAnalyticalThresholdRead"
    ] = None
    stutter_filter: Optional["StutterFilterRead"] = None


from app.schemas.application_analytical_threshold import (
    ApplicationAnalyticalThresholdRead,
)
from app.schemas.laboratory import LaboratoryRead
from app.schemas.statistical_software import StatisticalSoftwareRead
from app.schemas.stutter_filter import StutterFilterRead
