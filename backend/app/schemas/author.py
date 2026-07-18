from typing import Optional

from pydantic import BaseModel, ConfigDict


class AuthorBase(BaseModel):
    title: Optional[str] = None
    first_name: str
    last_name: str


class AuthorCreate(AuthorBase):
    pass


class AuthorRead(AuthorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
