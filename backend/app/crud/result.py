from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.crud.exceptions import DatabaseCommitError
from app.models.pcr import PCR
from app.models.result import Result
from app.schemas.result import ResultCreate, ResultUpdate


def _pcrs_from(pcrs) -> list[PCR]:
    return [PCR(**pcr_in.model_dump(exclude_none=True)) for pcr_in in pcrs]


class CRUDResult(CRUDBase[Result, ResultCreate, ResultUpdate]):
    def __init__(self):
        super().__init__(Result)

    async def create(self, db: AsyncSession, obj_in: ResultCreate) -> Result:
        obj_data = obj_in.model_dump(
            exclude={"pcrs"}, exclude_none=True, exclude_unset=True
        )
        new_result = Result(**obj_data)
        new_result.pcrs = _pcrs_from(obj_in.pcrs)
        db.add(new_result)

        try:
            await db.commit()
            await db.refresh(new_result)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return new_result

    async def update(self, db: AsyncSession, id: int, obj_in: ResultUpdate) -> Result:
        result = await self.get(db, id)
        update_data = obj_in.model_dump(
            exclude={"pcrs"}, exclude_none=True, exclude_unset=True
        )
        for field, value in update_data.items():
            setattr(result, field, value)

        if obj_in.pcrs is not None:
            result.pcrs = _pcrs_from(obj_in.pcrs)

        try:
            await db.commit()
            await db.refresh(result)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return result


crud_result = CRUDResult()
