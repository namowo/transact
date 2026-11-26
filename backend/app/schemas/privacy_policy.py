from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.site_settings import LegalPageMode

PrivacyPolicyStatus = Literal["draft", "active", "archived"]


class PrivacyPolicyDraftWrite(BaseModel):
    mode: Optional[LegalPageMode] = None
    text: Optional[str] = None
    url: Optional[str] = None


class PrivacyPolicyPublish(BaseModel):
    # Email every user that the policy changed.
    notify_users: bool = True


class PrivacyPolicyConsentCreate(BaseModel):
    privacy_policy_id: int


class PersonBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    first_name: str
    last_name: str


class PrivacyPolicyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version: Optional[int] = None
    mode: LegalPageMode
    text: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[datetime] = None


class PrivacyPolicyAdminRead(PrivacyPolicyRead):
    status: PrivacyPolicyStatus
    created_at: datetime
    updated_at: datetime
    created_by: Optional[PersonBrief] = None
    published_by: Optional[PersonBrief] = None
    # How many users agreed to this version.
    consent_count: int = 0
