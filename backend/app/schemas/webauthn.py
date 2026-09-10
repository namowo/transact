from datetime import datetime
from typing import Any, Dict, Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr


class WebAuthnRegisterVerify(BaseModel):
    credential: Dict[str, Any]
    device_name: Optional[str] = None


class WebAuthnLoginOptionsRequest(BaseModel):
    email: Optional[EmailStr] = None


class WebAuthnLoginVerify(BaseModel):
    email: Optional[EmailStr] = None
    credential: Dict[str, Any]


class WebAuthnCredentialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_name: Optional[str] = None
    created_at: datetime
    last_used_at: Optional[datetime] = None
