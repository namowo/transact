from typing import List, Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict

from app.schemas.epg_analysis_method_dye_channel_threshold import (
    EPGAnalysisMethodDyeChannelThresholdCreate,
    EPGAnalysisMethodDyeChannelThresholdRead,
)


class EPGAnalysisMethodBase(BaseModel):
    laboratory_id: Optional[UUID] = None
    genotyping_software_id: Optional[UUID] = None
    pcr_kit_id: Optional[UUID] = None
    application_analytical_threshold: Optional[str] = None
    stutter_filter_id: Optional[UUID] = None
    description: Optional[str] = None


class EPGAnalysisMethodCreate(EPGAnalysisMethodBase):
    dye_channel_thresholds: List[EPGAnalysisMethodDyeChannelThresholdCreate] = []


class EPGAnalysisMethodUpdate(EPGAnalysisMethodBase):
    dye_channel_thresholds: Optional[List[EPGAnalysisMethodDyeChannelThresholdCreate]] = None


class EPGAnalysisMethodRead(EPGAnalysisMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    laboratory: Optional["LaboratoryRead"] = None
    genotyping_software: Optional["GenotypingSoftwareRead"] = None
    pcr_kit: Optional["PCRKitRead"] = None
    stutter_filter: Optional["StutterFilterRead"] = None
    dye_channel_thresholds: List[EPGAnalysisMethodDyeChannelThresholdRead] = []


from app.schemas.laboratory import LaboratoryRead
from app.schemas.genotyping_software import GenotypingSoftwareRead
from app.schemas.pcr_kit import PCRKitRead
from app.schemas.stutter_filter import StutterFilterRead
