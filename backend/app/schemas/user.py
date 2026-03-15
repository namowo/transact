from pydantic import BaseModel, ConfigDict, EmailStr
from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate
from typing import Optional
from enum import Enum
from datetime import datetime
from uuid import UUID


class UserRead(BaseUser[UUID]):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    vorname: str
    nachname: str
    organisation: str
    telefon: Optional[str] = None
    strasse: str
    hausnummer: str
    stadt: str
    plz: str
    land: str
    erstellt_am: datetime


class UserCreate(BaseUserCreate):

    vorname: str
    nachname: str
    organisation: str
    telefon: Optional[str] = None
    strasse: str
    hausnummer: str
    stadt: str
    plz: str
    land: str


class UserUpdate(BaseUserUpdate):
    vorname: Optional[str] = None
    nachname: Optional[str] = None
    organisation: Optional[str] = None
    telefon: Optional[str] = None
    strasse: Optional[str] = None
    hausnummer: Optional[str] = None
    stadt: Optional[str] = None
    plz: Optional[str] = None
    land: Optional[str] = None
