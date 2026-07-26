from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.contact_template import ContactTemplate
from app.models.persistence import Persistence
from app.models.scenario import Scenario
from app.models.study import Study
from app.schemas.scenario import ScenarioCreate, ScenarioUpdate

ASSOCIATION_FIELDS = {
    "study_ids": (Study, "studies"),
    "contact_template_ids": (ContactTemplate, "contact_templates"),
    "persistence_ids": (Persistence, "persistencies"),
}


class CRUDScenario(CRUDBase[Scenario, ScenarioCreate, ScenarioUpdate]):
    def __init__(self):
        super().__init__(Scenario)

    async def create(self, db: AsyncSession, obj_in: ScenarioCreate) -> Scenario:
        return await self.create_with_associations(
            db, obj_in, association_fields=ASSOCIATION_FIELDS
        )

    async def update(
        self, db: AsyncSession, id: int, obj_in: ScenarioUpdate
    ) -> Scenario:
        return await self.update_with_associations(
            db, id, obj_in, association_fields=ASSOCIATION_FIELDS
        )


crud_scenario = CRUDScenario()
