from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ScrapingDeviceBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ScrapingDeviceCreate(ScrapingDeviceBase):
    pass


class ScrapingDeviceUpdate(ScrapingDeviceBase):
    pass


class ScrapingDeviceRead(ScrapingDeviceBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
