from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.individual import Individual
from app.models.scenario import Scenario
from app.schemas.individual import IndividualCreate, IndividualUpdate


ASSOCIATION_FIELDS = {
    "scenario_ids": (Scenario, "scenarios"),
}


class CRUDIndividual(CRUDBase[Individual, IndividualCreate, IndividualUpdate]):
    def __init__(self):
        super().__init__(Individual)

    async def create(self, db: AsyncSession, obj_in: IndividualCreate) -> Individual:
        return await self.create_with_associations(
            db, obj_in, association_fields=ASSOCIATION_FIELDS
        )

    async def update(
        self, db: AsyncSession, id: UUID, obj_in: IndividualUpdate
    ) -> Individual:
        return await self.update_with_associations(
            db, id, obj_in, association_fields=ASSOCIATION_FIELDS
        )

    async def get_all_for_study(self, db: AsyncSession, study_id: UUID) -> list[Individual]:
        result = await db.execute(
            select(Individual).where(Individual.study_id == study_id)
        )
        return list(result.scalars().all())


crud_individual = CRUDIndividual()
