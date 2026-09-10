from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.lab_membership_request import LabMembershipRequestStatus
from app.schemas.laboratory import LaboratoryCreate


class LabMembershipRequestCreateExisting(BaseModel):
    laboratory_id: UUID


class LabMembershipRequestCreateNewLab(LaboratoryCreate):
    pass


class LabMembershipRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    user: "UserRead"
    laboratory_id: UUID
    laboratory: "LaboratoryRead"
    status: LabMembershipRequestStatus
    reviewed_by_id: Optional[UUID] = None
    reviewed_by: Optional["UserRead"] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime


from app.schemas.laboratory import LaboratoryRead
from app.schemas.user import UserRead
