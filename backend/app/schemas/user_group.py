from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.permission_catalog import Permission, Scope


class PermissionRead(BaseModel):
    key: Permission
    label: str
    description: str
    scope: Scope


class UserGroupBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    system_key: Optional[str] = None
    laboratory_id: Optional[UUID] = None


class UserGroupRead(UserGroupBrief):
    description: Optional[str] = None
    permissions: List[Permission]
    member_count: int = 0


def _unique_permissions(value: Optional[List[Permission]]) -> Optional[List[Permission]]:
    if value is None:
        return None
    return sorted(set(value), key=lambda permission: permission.value)


class UserGroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    permissions: List[Permission] = []
    # Omit for a platform-wide group.
    laboratory_id: Optional[UUID] = None

    _unique = field_validator("permissions")(_unique_permissions)


class UserGroupUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    permissions: Optional[List[Permission]] = None

    _unique = field_validator("permissions")(_unique_permissions)


class UserGroupAssignment(BaseModel):
    group_ids: List[UUID]
