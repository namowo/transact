from typing import Optional

from pydantic import BaseModel, ConfigDict


class ScrapingMethodBase(BaseModel):
    scraping_device_id: Optional[int] = None
    description: Optional[str] = None
    supplier_id: Optional[int] = None


class ScrapingMethodCreate(ScrapingMethodBase):
    pass


class ScrapingMethodUpdate(ScrapingMethodBase):
    pass


class ScrapingMethodRead(ScrapingMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scraping_device: Optional["ScrapingDeviceRead"] = None
    supplier: Optional["SupplierRead"] = None


from app.schemas.scraping_device import ScrapingDeviceRead
from app.schemas.supplier import SupplierRead
