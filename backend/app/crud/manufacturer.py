from app.crud.base import CRUDBase
from app.models.manufacturer import Manufacturer
from app.schemas.manufacturer import ManufacturerCreate, ManufacturerUpdate


class CRUDManufacturer(CRUDBase[Manufacturer, ManufacturerCreate, ManufacturerUpdate]):
    def __init__(self):
        super().__init__(Manufacturer)


crud_manufacturer = CRUDManufacturer()
