from app.crud.base import CRUDBase
from app.models.scraping_device import ScrapingDevice
from app.schemas.scraping_device import ScrapingDeviceCreate, ScrapingDeviceUpdate


class CRUDScrapingDevice(CRUDBase[ScrapingDevice, ScrapingDeviceCreate, ScrapingDeviceUpdate]):
    def __init__(self):
        super().__init__(ScrapingDevice)


crud_scraping_device = CRUDScrapingDevice()
