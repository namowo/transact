from app.crud.base import CRUDBase
from app.models.thermoshaker import Thermoshaker
from app.schemas.thermoshaker import ThermoshakerCreate, ThermoshakerUpdate


class CRUDThermoshaker(CRUDBase[Thermoshaker, ThermoshakerCreate, ThermoshakerUpdate]):
    def __init__(self):
        super().__init__(Thermoshaker)


crud_thermoshaker = CRUDThermoshaker()
