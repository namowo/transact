from app.crud.base import CRUDBase
from app.models.individual import Individual
from app.schemas.individual import IndividualCreate, IndividualUpdate


class CRUDIndividual(CRUDBase[Individual, IndividualCreate, IndividualUpdate]):
    def __init__(self):
        super().__init__(Individual)


crud_individual = CRUDIndividual()
