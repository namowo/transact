from app.crud.base import CRUDBase
from app.models.thermocycler import Thermocycler
from app.schemas.thermocycler import ThermocyclerCreate, ThermocyclerUpdate


class CRUDThermocycler(CRUDBase[Thermocycler, ThermocyclerCreate, ThermocyclerUpdate]):
    def __init__(self):
        super().__init__(Thermocycler)


crud_thermocycler = CRUDThermocycler()
