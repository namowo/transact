from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ExtractionMethodLysisBufferComponentBase(BaseModel):
    lysis_buffer_component_id: Optional[UUID] = None
    volume: Optional[float] = None
    position: int = 0


class ExtractionMethodLysisBufferComponentCreate(ExtractionMethodLysisBufferComponentBase):
    pass


class ExtractionMethodLysisBufferComponentRead(ExtractionMethodLysisBufferComponentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lysis_buffer_component: Optional["LysisBufferComponentRead"] = None


from app.schemas.lysis_buffer_component import LysisBufferComponentRead
