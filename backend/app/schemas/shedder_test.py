from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ShedderTestBase(BaseModel):
    name: Optional[str] = None


class ShedderTestCreate(ShedderTestBase):
    pass


class ShedderTestUpdate(ShedderTestBase):
    pass


class ShedderTestRead(ShedderTestBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
