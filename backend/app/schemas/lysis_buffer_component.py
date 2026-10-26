from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class LysisBufferComponentBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class LysisBufferComponentCreate(LysisBufferComponentBase):
    pass


class LysisBufferComponentUpdate(LysisBufferComponentBase):
    pass


class LysisBufferComponentRead(LysisBufferComponentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
