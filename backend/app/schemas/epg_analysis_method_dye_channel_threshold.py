from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class EPGAnalysisMethodDyeChannelThresholdBase(BaseModel):
    dye_channel_id: Optional[UUID] = None
    analytical_threshold: Optional[float] = None
    position: int = 0


class EPGAnalysisMethodDyeChannelThresholdCreate(EPGAnalysisMethodDyeChannelThresholdBase):
    pass


class EPGAnalysisMethodDyeChannelThresholdRead(EPGAnalysisMethodDyeChannelThresholdBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dye_channel: Optional["DyeChannelRead"] = None


from app.schemas.dye_channel import DyeChannelRead
