from typing import Optional

from pydantic import BaseModel, ConfigDict


class TapeMethodBase(BaseModel):
    type_of_tape_id: Optional[int] = None
    description: Optional[str] = None
    catalogue_number_of_supplier: Optional[str] = None
    full_name_as_by_supplier: Optional[str] = None
    supplier: Optional[str] = None


class TapeMethodCreate(TapeMethodBase):
    pass


class TapeMethodUpdate(TapeMethodBase):
    pass


class TapeMethodRead(TapeMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type_of_tape: Optional["TypeOfTapeRead"] = None


from app.schemas.type_of_tape import TypeOfTapeRead
