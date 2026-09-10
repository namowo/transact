from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ApplicationAnalyticalThresholdBase(BaseModel):
    name: Optional[str] = None


class ApplicationAnalyticalThresholdCreate(ApplicationAnalyticalThresholdBase):
    pass


class ApplicationAnalyticalThresholdUpdate(ApplicationAnalyticalThresholdBase):
    pass


class ApplicationAnalyticalThresholdRead(ApplicationAnalyticalThresholdBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
