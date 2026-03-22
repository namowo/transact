from app.crud.base import CRUDBase
from app.models.scenario_category import ScenarioCategory
from app.schemas.scenario_category import ScenarioCategoryCreate, ScenarioCategoryUpdate


class CRUDScenarioCategory(CRUDBase[ScenarioCategory, ScenarioCategoryCreate, ScenarioCategoryUpdate]):
    def __init__(self):
        super().__init__(ScenarioCategory)


crud_scenario_category = CRUDScenarioCategory()
