from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ScrapingMethodBase(BaseModel):
    scraping_device_id: Optional[UUID] = None
    description: Optional[str] = None
    supplier_id: Optional[UUID] = None


class ScrapingMethodCreate(ScrapingMethodBase):
    pass


class ScrapingMethodUpdate(ScrapingMethodBase):
    pass


class ScrapingMethodRead(ScrapingMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scraping_device: Optional["ScrapingDeviceRead"] = None
    supplier: Optional["SupplierRead"] = None


from app.schemas.scraping_device import ScrapingDeviceRead
from app.schemas.supplier import SupplierRead
