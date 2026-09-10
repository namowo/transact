from typing import Optional

from uuid import UUID
from pydantic import BaseModel, ConfigDict


class TapeMethodBase(BaseModel):
    type_of_tape_id: Optional[UUID] = None
    description: Optional[str] = None
    supplier_id: Optional[UUID] = None


class TapeMethodCreate(TapeMethodBase):
    pass


class TapeMethodUpdate(TapeMethodBase):
    pass


class TapeMethodRead(TapeMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type_of_tape: Optional["TypeOfTapeRead"] = None
    supplier: Optional["SupplierRead"] = None


from app.schemas.type_of_tape import TypeOfTapeRead
from app.schemas.supplier import SupplierRead
