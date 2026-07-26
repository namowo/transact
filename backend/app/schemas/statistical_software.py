from typing import Optional

from pydantic import BaseModel, ConfigDict


class StatisticalSoftwareBase(BaseModel):
    name: Optional[str] = None


class StatisticalSoftwareCreate(StatisticalSoftwareBase):
    pass


class StatisticalSoftwareUpdate(StatisticalSoftwareBase):
    pass


class StatisticalSoftwareRead(StatisticalSoftwareBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
