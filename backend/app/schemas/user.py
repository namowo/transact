from datetime import datetime
from typing import Dict, List, Literal, Optional
from uuid import UUID

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
    groups: List["UserGroupBrief"] = []
    # Union of the groups' permissions (see app.core.permission_catalog).
    permissions: List[str] = []
    passkey_prompt_dismissed: bool
    completed_tours: List[str] = []
    locale: str = "en-US"
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
