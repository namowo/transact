from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.individual import Individual
from app.schemas.individual import IndividualCreate, IndividualUpdate


class CRUDIndividual(CRUDBase[Individual, IndividualCreate, IndividualUpdate]):
    def __init__(self):
        super().__init__(Individual)

    async def get_all_for_study(self, db: AsyncSession, study_id: UUID) -> list[Individual]:
        result = await db.execute(
            select(Individual).where(Individual.study_id == study_id)
        )
        return list(result.scalars().all())


crud_individual = CRUDIndividual()
