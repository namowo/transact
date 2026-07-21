from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    laboratory_id: Optional[int] = None


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    laboratory_id: Optional[int] = None


class LaboratoryAssignment(BaseModel):
    laboratory_id: Optional[int] = None


class EmailChange(BaseModel):
    current_password: str
    new_email: EmailStr


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool
    is_verified: bool
    is_superuser: bool
    can_quality_check: bool
    can_manage_lab_users: bool
    passkey_prompt_dismissed: bool
    laboratory_id: Optional[int] = None
    laboratory: Optional["LaboratoryRead"] = None
    created_at: datetime


from app.schemas.laboratory import LaboratoryRead
