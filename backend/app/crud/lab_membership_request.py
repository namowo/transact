from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.crud.base import CRUDBase
from app.crud.exceptions import ConflictError, DatabaseCommitError
from app.models.laboratory import Laboratory, LaboratoryApprovalStatus
from app.models.lab_membership_request import (
    LabMembershipRequest,
    LabMembershipRequestStatus,
)
from app.models.user import User
from app.schemas.laboratory import LaboratoryCreate
from app.schemas.lab_membership_request import (
    LabMembershipRequestCreateExisting,
    LabMembershipRequestCreateNewLab,
)


class CRUDLabMembershipRequest(
    CRUDBase[
        LabMembershipRequest,
        LabMembershipRequestCreateExisting,
        LabMembershipRequestCreateNewLab,
    ]
):
    def __init__(self):
        super().__init__(LabMembershipRequest)

    async def get_pending_for_user(
        self, db: AsyncSession, user_id: int
    ) -> Optional[LabMembershipRequest]:
        statement = select(self.model).where(
            self.model.user_id == user_id,
            self.model.status == LabMembershipRequestStatus.pending,
        )
        result = await db.execute(statement)
        return result.scalars().first()

    async def list_pending_for_laboratory(
        self, db: AsyncSession, laboratory_id: int
    ) -> List[LabMembershipRequest]:
        statement = select(self.model).where(
            self.model.laboratory_id == laboratory_id,
            self.model.status == LabMembershipRequestStatus.pending,
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def list_pending_new_labs(
        self, db: AsyncSession
    ) -> List[LabMembershipRequest]:
        statement = (
            select(self.model)
            .join(Laboratory, self.model.laboratory_id == Laboratory.id)
            .where(
                self.model.status == LabMembershipRequestStatus.pending,
                Laboratory.approval_status == LaboratoryApprovalStatus.pending,
            )
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def create_join_request(
        self, db: AsyncSession, user: User, laboratory_id: int
    ) -> LabMembershipRequest:
        if await self.get_pending_for_user(db, user.id):
            raise ConflictError(message="You already have a pending request.")

        request = LabMembershipRequest(user_id=user.id, laboratory_id=laboratory_id)
        db.add(request)
        try:
            await db.commit()
            await db.refresh(request)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return request

    async def create_new_lab_request(
        self, db: AsyncSession, user: User, laboratory_in: LaboratoryCreate
    ) -> LabMembershipRequest:
        if await self.get_pending_for_user(db, user.id):
            raise ConflictError(message="You already have a pending request.")

        new_laboratory = Laboratory(
            **laboratory_in.model_dump(exclude_none=True, exclude_unset=True),
            approval_status=LaboratoryApprovalStatus.pending,
        )
        db.add(new_laboratory)

        try:
            await db.flush()
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        request = LabMembershipRequest(
            user_id=user.id, laboratory_id=new_laboratory.id
        )
        db.add(request)

        try:
            await db.commit()
            await db.refresh(request)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return request

    async def approve(
        self, db: AsyncSession, request: LabMembershipRequest, reviewer: User
    ) -> LabMembershipRequest:
        is_new_lab = request.laboratory.approval_status == LaboratoryApprovalStatus.pending

        request.status = LabMembershipRequestStatus.approved
        request.reviewed_by_id = reviewer.id
        request.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)

        request.user.laboratory_id = request.laboratory_id

        if is_new_lab:
            request.laboratory.approval_status = LaboratoryApprovalStatus.approved
            request.user.can_manage_lab_users = True

        try:
            await db.commit()
            await db.refresh(request)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return request

    async def deny(
        self, db: AsyncSession, request: LabMembershipRequest, reviewer: User
    ) -> LabMembershipRequest:
        is_new_lab = request.laboratory.approval_status == LaboratoryApprovalStatus.pending

        request.status = LabMembershipRequestStatus.denied
        request.reviewed_by_id = reviewer.id
        request.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)

        if is_new_lab:
            request.laboratory.approval_status = LaboratoryApprovalStatus.denied

        try:
            await db.commit()
            await db.refresh(request)
        except SQLAlchemyError as e:
            await db.rollback()
            raise DatabaseCommitError(message=str(e))

        return request


crud_lab_membership_request = CRUDLabMembershipRequest()
