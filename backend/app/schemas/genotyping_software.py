from typing import Optional

from pydantic import BaseModel, ConfigDict


class GenotypingSoftwareBase(BaseModel):
    name: Optional[str] = None


class GenotypingSoftwareCreate(GenotypingSoftwareBase):
    pass


class GenotypingSoftwareUpdate(GenotypingSoftwareBase):
    pass


class GenotypingSoftwareRead(GenotypingSoftwareBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
