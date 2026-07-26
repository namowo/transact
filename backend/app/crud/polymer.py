from app.crud.base import CRUDBase
from app.models.polymer import Polymer
from app.schemas.polymer import PolymerCreate, PolymerUpdate


class CRUDPolymer(CRUDBase[Polymer, PolymerCreate, PolymerUpdate]):
    def __init__(self):
        super().__init__(Polymer)


crud_polymer = CRUDPolymer()
