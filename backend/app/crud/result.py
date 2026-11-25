from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.crud.exceptions import DatabaseCommitError
from app.models.pcr import PCR
from app.models.pcr_contributor import PCRContributor
from app.models.result import Result
from app.schemas.result import ResultCreate, ResultUpdate


def _pcrs_from(pcrs) -> list[PCR]:
    result = []
    for pcr_in in pcrs:
        data = pcr_in.model_dump(exclude={"contributors"}, exclude_none=True)
        pcr = PCR(**data)
        pcr.contributors = [
            PCRContributor(**contributor_in.model_dump(exclude_none=True))
            for contributor_in in pcr_in.contributors
        ]
        result.append(pcr)
    return result


def _derive_dna_input_amounts(result: Result) -> None:
    """DNA input amount in PCR (pg) = DNA concentration (ng/µl) x sample
    input volume (µl) x 1000. Recalculated on every save so it follows later
    edits of the concentration; left as entered when either value is missing."""
    if result.dna_concentration is None:
        return
    for pcr in result.pcrs:
        if pcr.sample_input_volume_in_pcr is not None:
            pcr.dna_input_amount_in_pcr = (
                result.dna_concentration * pcr.sample_input_volume_in_pcr * 1000
            )


class CRUDResult(CRUDBase[Result, ResultCreate, ResultUpdate]):
    def __init__(self):
        super().__init__(Result)

    async def create(self, db: AsyncSession, obj_in: ResultCreate) -> Result:
        obj_data = obj_in.model_dump(
            exclude={"pcrs"}, exclude_none=True, exclude_unset=True
        )
        new_result = Result(**obj_data)
        new_result.pcrs = _pcrs_from(obj_in.pcrs)
        _derive_dna_input_amounts(new_result)
        db.add(new_result)

        try:
            await db.commit()
            await db.refresh(new_result)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return new_result

    async def update(self, db: AsyncSession, id: UUID, obj_in: ResultUpdate) -> Result:
        result = await self.get(db, id)
        update_data = obj_in.model_dump(
            exclude={"pcrs"}, exclude_none=True, exclude_unset=True
        )
        for field, value in update_data.items():
            setattr(result, field, value)

        if obj_in.pcrs is not None:
            result.pcrs = _pcrs_from(obj_in.pcrs)
        _derive_dna_input_amounts(result)

        try:
            await db.commit()
            await db.refresh(result)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return result


crud_result = CRUDResult()
