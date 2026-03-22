from app.crud.base import CRUDBase
from app.models.scraping_method import ScrapingMethod
from app.schemas.scraping_method import ScrapingMethodCreate, ScrapingMethodUpdate


class CRUDScrapingMethod(CRUDBase[ScrapingMethod, ScrapingMethodCreate, ScrapingMethodUpdate]):
    def __init__(self):
        super().__init__(ScrapingMethod)


crud_scraping_method = CRUDScrapingMethod()
