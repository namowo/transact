from datetime import datetime
from typing import Dict, List, Literal, Optional
from uuid import UUID

from app.core.notification_catalog import (
    NOTIFICATION_TYPE_INFO,
    Channel,
    NotificationType,
)
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# Data tables whose column sort is saved on the user.
SortableTable = Literal["samples", "results"]


class TableSortMeta(BaseModel):
    field: str = Field(max_length=100, pattern=r"^[A-Za-z0-9_.]+$")
    order: Literal[1, -1]


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    laboratory_id: Optional[UUID] = None


class UserCreate(UserBase):
    password: str = Field(min_length=8)
    # The privacy policy version the user agreed to while signing up; must
    # be the active one, if there is one.
    privacy_policy_id: Optional[int] = None


class SetupStatus(BaseModel):
    needs_setup: bool


class SuperuserSetup(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str
    last_name: str


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    locale: Optional[str] = Field(
        default=None, pattern=r"^[a-z]{2,3}(-[A-Za-z0-9]{2,8})*$", max_length=35
    )
    # Partial: only the given types and channels change.
    notification_settings: Optional[Dict[NotificationType, Dict[Channel, bool]]] = None
    # No laboratory_id: users join a laboratory through a membership request
    # (or an admin moves them), never by editing their own profile.
    table_sorts: Optional[Dict[SortableTable, List[TableSortMeta]]] = None

    @field_validator("table_sorts")
    @classmethod
    def unique_sort_fields(cls, value: Optional[Dict[str, List[TableSortMeta]]]):
        for metas in (value or {}).values():
            if len(metas) > 20:
                raise ValueError("Too many sort columns.")
            if len({meta.field for meta in metas}) != len(metas):
                raise ValueError("Each column may only be sorted once.")
        return value

    @field_validator("notification_settings")
    @classmethod
    def supported_channels(cls, value):
        for type, channels in (value or {}).items():
            supported = NOTIFICATION_TYPE_INFO[type].defaults
            for channel in channels:
                if channel not in supported:
                    raise ValueError(
                        f"{type.value} notifications can't be sent by {channel}."
                    )
        return value


class NotificationTypeRead(BaseModel):
    key: NotificationType
    label: str
    description: str
    channels: List[Channel]


class UserInvite(BaseModel):
    email: EmailStr
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    # Lab admins can only invite to their own laboratory, which is used when
    # this is left out.
    laboratory_id: Optional[UUID] = None
    group_ids: List[UUID] = []


class LaboratoryAssignment(BaseModel):
    laboratory_id: Optional[UUID] = None


class EmailChange(BaseModel):
    current_password: str
    new_email: EmailStr


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool
    is_verified: bool
    # Too many wrong passwords; an admin has to unlock the account.
    is_locked: bool = False
    invitation_pending: bool = False
    groups: List["UserGroupBrief"] = []
    # Union of the groups' permissions (see app.core.permission_catalog).
    permissions: List[str] = []
    passkey_prompt_dismissed: bool
    totp_enabled: bool = False
    recovery_codes_remaining: int = 0
    # Only on the signed-in user: they must set up a second factor before
    # they can use the app.
    two_factor_setup_required: bool = False
    completed_tours: List[str] = []
    # Privacy policy versions (ids) the user agreed to. Once a newer version
    # is published, they have to agree to it before using the app.
    accepted_privacy_policy_ids: List[int] = []
    locale: str = "en-US"
    # Every type's channels, with defaults filled in.
    notification_settings: Dict[str, Dict[str, bool]] = Field(
        default={}, validation_alias="resolved_notification_settings"
    )
    table_sorts: Optional[Dict[str, List[TableSortMeta]]] = None
    laboratory_id: Optional[UUID] = None
    laboratory: Optional["LaboratoryRead"] = None
    created_at: datetime


    @field_validator("permissions", mode="before")
    @classmethod
    def sorted_permissions(cls, value):
        return sorted(value or [])


from app.schemas.laboratory import LaboratoryRead
from app.schemas.user_group import UserGroupBrief
