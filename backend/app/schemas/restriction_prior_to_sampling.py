from typing import Optional

from pydantic import BaseModel, ConfigDict


class RestrictionPriorToSamplingBase(BaseModel):
    name: Optional[str] = None


class RestrictionPriorToSamplingCreate(RestrictionPriorToSamplingBase):
    pass


class RestrictionPriorToSamplingUpdate(RestrictionPriorToSamplingBase):
    pass


class RestrictionPriorToSamplingRead(RestrictionPriorToSamplingBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
