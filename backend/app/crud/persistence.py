from app.crud.base import CRUDBase
from app.models.persistence import Persistence
from app.schemas.persistence import PersistenceCreate, PersistenceUpdate


class CRUDPersistence(CRUDBase[Persistence, PersistenceCreate, PersistenceUpdate]):
    def __init__(self):
        super().__init__(Persistence)


crud_persistence = CRUDPersistence()
