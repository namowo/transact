from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class SampleSetBase(BaseModel):
    name: Optional[str] = None


class SampleSetCreate(SampleSetBase):
    pass


class SampleSetUpdate(SampleSetBase):
    pass


class SampleSetRead(SampleSetBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
