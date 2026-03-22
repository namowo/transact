from app.crud.base import CRUDBase
from app.models.scenario import Scenario
from app.schemas.scenario import ScenarioCreate, ScenarioUpdate


class CRUDScenario(CRUDBase[Scenario, ScenarioCreate, ScenarioUpdate]):
    def __init__(self):
        super().__init__(Scenario)


crud_scenario = CRUDScenario()
