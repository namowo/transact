from typing import Optional

from pydantic import BaseModel, ConfigDict


class ScrapingMethodBase(BaseModel):
    scraping_device_id: Optional[int] = None
    description: Optional[str] = None
    catalogue_number_of_supplier: Optional[str] = None
    full_name_as_by_supplier: Optional[str] = None
    supplier: Optional[str] = None


class ScrapingMethodCreate(ScrapingMethodBase):
    pass


class ScrapingMethodUpdate(ScrapingMethodBase):
    pass


class ScrapingMethodRead(ScrapingMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scraping_device: Optional["ScrapingDeviceRead"] = None


from app.schemas.scraping_device import ScrapingDeviceRead
