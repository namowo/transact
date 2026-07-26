from typing import Optional

from pydantic import BaseModel, ConfigDict


class TypeOfFormamideBase(BaseModel):
    name: Optional[str] = None


class TypeOfFormamideCreate(TypeOfFormamideBase):
    pass


class TypeOfFormamideUpdate(TypeOfFormamideBase):
    pass


class TypeOfFormamideRead(TypeOfFormamideBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
