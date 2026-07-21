from typing import List

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.crud.base import CRUDBase
from app.crud.exceptions import DatabaseCommitError
from app.models.laboratory import Laboratory, LaboratoryApprovalStatus
from app.schemas.laboratory import LaboratoryCreate, LaboratoryUpdate


class CRUDLaboratory(CRUDBase[Laboratory, LaboratoryCreate, LaboratoryUpdate]):
    def __init__(self):
        super().__init__(Laboratory)

    async def list_approved(self, db: AsyncSession) -> List[Laboratory]:
        statement = select(self.model).where(
            self.model.approval_status == LaboratoryApprovalStatus.approved
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def list_pending(self, db: AsyncSession) -> List[Laboratory]:
        statement = select(self.model).where(
            self.model.approval_status == LaboratoryApprovalStatus.pending
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def set_approval_status(
        self,
        db: AsyncSession,
        laboratory: Laboratory,
        status: LaboratoryApprovalStatus,
    ) -> Laboratory:
        laboratory.approval_status = status
        try:
            await db.commit()
            await db.refresh(laboratory)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return laboratory


crud_laboratory = CRUDLaboratory()
