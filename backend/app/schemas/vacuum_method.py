from typing import Optional

from pydantic import BaseModel, ConfigDict


class VacuumMethodBase(BaseModel):
    vacuum_device: Optional[str] = None
    description: Optional[str] = None
    catalogue_number_of_supplier: Optional[str] = None
    full_name_as_by_supplier: Optional[str] = None
    supplier: Optional[str] = None


class VacuumMethodCreate(VacuumMethodBase):
    pass


class VacuumMethodUpdate(VacuumMethodBase):
    pass


class VacuumMethodRead(VacuumMethodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
